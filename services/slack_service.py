import time
import asyncio
from collections import defaultdict, namedtuple

import slack
from addict import Dict

from consts.slack_models import EnvironmentConfig, SubscribersConfig, EnvInfo
from qa_tool.utils.utils import to_list
from qa_tool.utils.common import StatusCodes
from qa_tool.utils.validator import validate
from libs import PortainerInterface, slack_bot
from consts.infrastructure import ServiceScope, Environment
from services.service_settings import SLACK_TOKEN, SLACK_TO_PORTAINER_HOOK_TIMEOUT, PORTAINER_URL


EXCLUDE_IMAGES = [
    'zookeeper',
    'redis',
    'balancer',
    'prometheus',
    'consul',
    'postgres',
    'kafka',
    'pgbouncer',
    'rabbitmq',
]

ENV_COLOR = {
    Environment.DEV: '#FFF000',
    Environment.STAGE: '#235789',
    Environment.PROD: '#C1292E',
}


class Commands:
    _CHANNELS_FILE = 'slack_subs_channel.json'
    _ENVIRONMENT_FILE = 'slack_environments_config.json'

    def __save_subs(self):
        slack_bot.save_config(self._CHANNELS_FILE, self.SUBSCRIBED_CHANNELS, SubscribersConfig)

    def _save_env_config(self):
        slack_bot.save_config(self._ENVIRONMENT_FILE, self.ENVIRONMENTS_CONFIG, EnvironmentConfig)

    def __init__(self):
        print(f"Start init slack commands")
        _channel_file_data = slack_bot.init_config(self._CHANNELS_FILE)
        _env_conf_file_data = slack_bot.init_config(self._ENVIRONMENT_FILE)
        print(f"Configuration files was opened")
        print(f"Start serialize configs")
        self.SUBSCRIBED_CHANNELS = SubscribersConfig().load(_channel_file_data) if _channel_file_data else defaultdict(set) # like EnvInfo(): [list of channels]
        self.ENVIRONMENTS_CONFIG = EnvironmentConfig().load(_env_conf_file_data) if _env_conf_file_data else defaultdict(
            lambda: Dict({
                'services': defaultdict(set),
                'previous_services': defaultdict(set),
                'last_update': time.time(),
                'last_service_update': time.time(),
                'last_previous_service_update': time.time(),
        }))  # like EnvInfo(): last updated service scope information
        print(f"Serialize configs completed")
        self.updated_envs = []
        self._portainer = None

    @property
    def portainer(self):
        if self._portainer is None:
            self._portainer = PortainerInterface()
        return self._portainer

    def send_exception(self, *msg):
        return slack_bot.text('Some problem in execution', *msg)

    def get_interested_subs(self, env_obj: EnvInfo):
        return self.SUBSCRIBED_CHANNELS[env_obj]

    def _get_envs_info_by(self, scope, env) -> list:
        scopes = ServiceScope.get_all() if scope.lower() == 'all' else to_list(ServiceScope.find(scope))
        envs = Environment.get_all() if env.lower() == Environment.ALL.lower() else to_list(Environment.get_env_by_alias(env))
        result = []
        for i in self.ENVIRONMENTS_CONFIG.keys():
            if i.scope in scopes and i.env in envs:
                result.append(i)
        return result

    def prepare_env_infos(self):
        code, portainer_stacks = self.portainer.get_stacks()
        assert code == StatusCodes.OK

        for stack in portainer_stacks:
            if stack['Status'] == self.portainer.StackStatus.INACTIVE:
                continue
            name = stack['Name']
            if 'legacy connection' in name.lower():
                continue
            env_obj = EnvInfo(ServiceScope.find(name), Environment.find(name), str(stack['Id']), name)
            if env_obj not in self.ENVIRONMENTS_CONFIG:
                self.ENVIRONMENTS_CONFIG[env_obj].last_update = time.time()
            if env_obj not in self.SUBSCRIBED_CHANNELS:
                self.SUBSCRIBED_CHANNELS[env_obj] = set()

        for env_obj, services in self.ENVIRONMENTS_CONFIG.items():
            current_data = self._get_envs_containers(env_obj)
            try:
                validate(services.services, current_data)
                assert len(services.services) == len(current_data)
            except AssertionError:
                if services.last_service_update == services.last_previous_service_update:
                    services.last_service_update = time.time()
                if services.last_service_update + SLACK_TO_PORTAINER_HOOK_TIMEOUT + 10 < time.time():
                    print(f"Update {env_obj} in progress")
                    _time_now = time.time()
                    services.last_previous_service_update = _time_now
                    services.last_service_update = _time_now
                    services.previous_services = services.services
                    services.services = current_data
                    self.updated_envs.append(env_obj)
                    print(f"Added task for notify subscribers {env_obj}")

    def _get_envs_containers(self, env_obj, exclude_infra_services=True):
        code, containers = self.portainer.get_containers_by_stack(env_obj.id)
        assert code == StatusCodes.OK
        self.ENVIRONMENTS_CONFIG[env_obj].last_update = time.time()
        containers = [i for i in containers if i.get('State') == self.portainer.ContainerState.RUNNING]
        current_data = defaultdict(set)
        for container in containers:
            image = container.get('Image')
            if exclude_infra_services and any([i for i in EXCLUDE_IMAGES if i in image]):
                continue
            labels = container.get('Labels', {})
            svc_name = labels.get(self.portainer.CntLabel.SERVICE_NAME)
            if svc_name is None:
                continue
            _lbl = self.portainer.CntLabel
            version_info = '-'.join([labels.get(i, '') for i in [_lbl.BRANCH, _lbl.VERSION, _lbl.COMMIT]])
            current_data[svc_name].add(version_info)
        return current_data

    def get_help(self, channel_id):
        return channel_id, slack_bot.text(
            slack_bot.dict_to_str(SlackService.get_interested_fn_by_command, 'Some strange helper')
        )

    def subscribe_channel_to_environment(self, channel, service_scope=None, env=None):
        env_objs = self._get_envs_info_by(service_scope, env)
        if not env_objs:
            return channel, self.send_exception(f"Not found scope - '{service_scope}', env -'{env}'")
        for i in env_objs:
            self.SUBSCRIBED_CHANNELS[i].add(channel)
        channel, msg = self.get_environment_info(channel, service_scope, env)
        msg.update(slack_bot.text('Successfull subscribe this channel to services:', *[i.name for i in env_objs]))
        self.__save_subs()
        return channel, msg

    def __formatted_service_diff_map(self, old_services, new_services, show_old_version_necessarily):
        result = {}
        _fn = lambda data: list(data)[0] if len(data) == 1 else data
        for svc_name, new_versions in new_services.items():
            old_versions = old_services.get(svc_name, 'New service')
            if old_versions == new_versions and not show_old_version_necessarily:
                result[svc_name] = f"{_fn(new_versions)}"
            else:
                result[svc_name] = f"{_fn(old_versions)} -> {_fn(new_versions)}"
        return result

    def env_info_and_obj_to_msg(self, env_obj, env_info, show_old_version_necessarily=False):
        service_diff = self.__formatted_service_diff_map(
            env_info.previous_services, env_info.services, show_old_version_necessarily
        )
        fields = [
            slack_bot.get_field("Project", env_obj.scope),
            slack_bot.get_field("Environment", env_obj.env),
            slack_bot.get_field("Services", slack_bot.dict_to_str(service_diff), False),
        ]
        return slack_bot.get_attachment(
            fields,
            ENV_COLOR[env_obj.env],
            ts=str(int(env_info.last_service_update)),
            title=env_obj.name,
            title_link=f'{PORTAINER_URL}/#/dashboard?stack={env_obj.id}'
        )

    def get_environment_info(self, channel_id, scope, env):
        print(f'Get environment info for {channel_id}: ({scope}:{env})')
        env_objs = self._get_envs_info_by(scope, env)
        attachments = []
        err_msg = f"Got some problem when execute 'get_environment_info' for {scope} {env}"
        for env_obj in env_objs:
            if env_obj not in self.ENVIRONMENTS_CONFIG:
                self.send_exception(err_msg, f"Problem with {env_obj}")
                continue
            attach = self.env_info_and_obj_to_msg(
                env_obj, self.ENVIRONMENTS_CONFIG[env_obj], show_old_version_necessarily=True
            )
            attachments.append(attach)
        return channel_id, {'attachments': attachments}

    def post_updated_env_info(self):
        print(f"Check task for notify subscribers")
        if self.updated_envs:
            print(f"Saved new environment config")
            self._save_env_config()
            print(f"Saved new environment config")
        while self.updated_envs:
            env_obj = self.updated_envs.pop()
            attachments = self.env_info_and_obj_to_msg(env_obj, self.ENVIRONMENTS_CONFIG[env_obj])
            print(f"Start notify {env_obj} subs. Subs: {self.SUBSCRIBED_CHANNELS[env_obj]}")
            for channel in self.SUBSCRIBED_CHANNELS[env_obj]:
                slack_bot.service.chat_postMessage(channel=channel, **{'attachments': to_list(attachments)})


fake_fn = lambda i: i


class SlackService:
    COMMAND_INTERFACE = Commands()

    get_interested_fn_by_command = {
        'help': [COMMAND_INTERFACE.get_help],
        'hello': [lambda channel_id: (channel_id, slack_bot.text('Hello'))],
        'get': [COMMAND_INTERFACE.get_environment_info, fake_fn, fake_fn],
        'subscribe': [COMMAND_INTERFACE.subscribe_channel_to_environment, fake_fn, fake_fn],
    }

    def prepare_message(self, channel_id, message: str) -> (list, list):
        if not message.startswith('QA'):
            return None, None

        command_line = message.replace('QA ', '').lower().split(' ')
        command_name = command_line[0]
        preparation_fns = list(self.get_interested_fn_by_command.get(command_name, []))

        if preparation_fns is None or len(preparation_fns) != len(command_line):
            return None, None

        main_command_name = command_line.pop(0)
        command_fn = preparation_fns.pop(0)
        args = [channel_id]
        try:
            for i, sub_fn_arg in enumerate(command_line):
                data = preparation_fns[i](sub_fn_arg)
                args.append(data)
            channels, messages = command_fn(*args)
            return to_list(channels or channel_id), messages if messages is None else to_list(messages)
        except Exception as e:
            return to_list(channel_id), self.COMMAND_INTERFACE.send_exception(
                f"Can't execute {main_command_name}, with args {command_line}", str(e)
            )


slack_service = SlackService()


@slack.RTMClient.run_on(event='message')
async def environment_checker(**payload):
    data = payload['data']
    channel_ids, messages_struct = slack_service.prepare_message(data['channel'], data.get('text', ''))
    if messages_struct is None:
        return
    messages_struct = to_list(messages_struct)
    web_client = payload['web_client']
    for channel in channel_ids:
        for msg in messages_struct:
            await web_client.chat_postMessage(
                channel=channel,
                **msg,
                ts=str(time.time())
            )


async def fetch_environments():
    loop = asyncio.get_running_loop()
    while True:
        await loop.run_in_executor(None, slack_service.COMMAND_INTERFACE.prepare_env_infos)
        await asyncio.sleep(SLACK_TO_PORTAINER_HOOK_TIMEOUT)


async def check_updated_environment_scheduler():
    loop = asyncio.get_running_loop()
    while True:
        await loop.run_in_executor(None, slack_service.COMMAND_INTERFACE.post_updated_env_info)
        await asyncio.sleep(SLACK_TO_PORTAINER_HOOK_TIMEOUT/2)


async def slack_main():
    loop = asyncio.get_event_loop()
    rtm_client = slack.RTMClient(token=SLACK_TOKEN, run_async=True, loop=loop)
    print('Started QA slack service')
    loop.create_task(fetch_environments())
    loop.create_task(check_updated_environment_scheduler())
    await rtm_client.start()


if __name__ == "__main__":
    asyncio.run(slack_main())

    # rtm_client = slack.RTMClient(token=SLACK_TOKEN)
    # rtm_client.start()
#     comm = SlackService.COMMAND_INTERFACE
#     comm.prepare_env_infos()
    # pprint.pprint(dict(comm.ENVIRONMENTS_CONFIG))
    # for qwe in comm.ENVIRONMENTS_CONFIG.values():
    #     for k in qwe.services.keys():
    #         print(k)