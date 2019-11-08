import time
import slack
from collections import defaultdict

from addict import Dict

from libs.slack_bot import slack_bot
from qa_tool.utils.utils import generate_value
from consts.infrastructure import ServiceScope, Environment
from services.service_settings import SLACK_TOKEN, SLACK_TO_PORTAINER_HOOK_TIMEOUT

import asyncio
import concurrent


ENV_COLOR = {
    Environment.DEV: '#FFF000',
    Environment.STAGE: '#235789',
    Environment.PROD: '#C1292E',
}


keks_msg = [
    {
        # "text": "UI is not defined",
        "fields": [
            {
                "title": "Project",
                "value": "Awesome Project",
                "short": True
            },
            {
                "title": "Environment",
                "value": "production",
                "short": True
            },
            {
                "title": "Services",
                "value": slack_bot.dict_to_str({i: generate_value(20, 'super-commit') for i in ServiceScope.get_all()}),
                "short": False
            }
        ],
        "color": "#F35A00",
        "ts": str(time.time())
    }
]


class Commands:

    CHANNELS_FILE = 'subs_channel.json'
    ENVIRONMENT_FILE = 'environments_config.json'

    def __init__(self):
        subs_config = slack_bot.init_config(self.CHANNELS_FILE) or defaultdict(list)
        environment_config = slack_bot.init_config(self.ENVIRONMENT_FILE)
        self.subscribed_channels = defaultdict(list)  # like (ServiceScope, Environment): [list of channels]
        self.environments_config = defaultdict(lambda: Dict({
           'services': dict(),
           'last_update': time.time(),
        }))  # like (ServiceScope, Environment): last updated service scope information

    def get_help(self):
        return slack_bot.dict_to_str(self.get_interested_fn_by_command, 'Some strange helper')

    def send_exception(self, *msg):
        return slack_bot.text('Some problem in execution', *msg)

    def subs_to_send_env_info(self, service_scope, env):
        return

    def get_portainer_envs(self):
        return

    def update_saved_environments(self):
        return


class SlackService:
    COMMAND_INTERFACE = Commands()

    get_interested_fn_by_command = {
        'subscribe': [COMMAND_INTERFACE.subs_to_send_env_info, ServiceScope.find, Environment.find],
        'help': [COMMAND_INTERFACE.get_help],
        'hello': [lambda: slack_bot.text('Hello')]
    }

    def message_performer(self, message: str):
        if not message.startswith('QA'):
            return

        command_line = message.replace('QA ', '').lower().split(' ')
        command_name = command_line[0]
        preparation_fns = self.get_interested_fn_by_command.get(command_name)

        if preparation_fns is None or len(preparation_fns) != len(command_line):
            return

        main_command_name = command_line.pop(0)
        command_fn = preparation_fns.pop(0)
        args = []
        try:
            for i, sub_fn_arg in enumerate(command_line):
                    data = preparation_fns[i](sub_fn_arg)
                    args.append(data)
            return command_fn(*args)
        except Exception as e:
            return Commands.send_exception(f"Can't execute {main_command_name}, with args {command_line}", str(e))


slack_service = SlackService()


@slack.RTMClient.run_on(event='message')
def environment_checker(**payload):
    data = payload['data']
    message_struct = slack_service.message_performer(data.get('text', ''))
    if message_struct is None:
        return
    channel_id = data['channel']
    web_client = payload['web_client']
    web_client.chat_postMessage(
        channel=channel_id,
        **message_struct,
        ts=str(time.time())
    )


async def environments_worker():
    while True:
        Commands.processing_portainer_envs()
        time.sleep(SLACK_TO_PORTAINER_HOOK_TIMEOUT)


# web_client.chat_postMessage(
#         channel=channel_id,
#         attachments=keks_msg,
#         **message_struct
#     )

print('keks')
rtm_client = slack.RTMClient(token=SLACK_TOKEN)
rtm_client.start()
# async def slack_main():
#     loop = asyncio.get_event_loop()
#     rtm_client = slack.RTMClient(token=SLACK_TOKEN, run_async=True, loop=loop)
#     executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
#     await asyncio.gather(
#         # loop.run_in_executor(executor, environment_checker),
#         rtm_client.start()
#     )
#
#
# if __name__ == "__main__":
#     asyncio.run(slack_main())
