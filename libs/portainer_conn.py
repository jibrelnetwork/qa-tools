import os
from typing import List

from cachetools.func import ttl_cache

from qa_tool.static.infrastructure import ServiceScope, Environment
from consts.slack_models import EnvInfo
from qa_tool.libs.reporter import reporter
from qa_tool.utils.common import ClientApi, StatusCodes
from qa_tool.utils.utils import getter
from services.service_settings import PORTAINER_TOKEN_LIFETIME, PORTAINER_USER, PORTAINER_PASSWORD, PORTAINER_URL

PORTAINER_TTL_CACHE = int(os.getenv('PORTAINER_TTL_CACHE', '3'))

API_AUTH_HEADER = 'Authorization'


@ttl_cache(ttl=PORTAINER_TOKEN_LIFETIME)
def get_portainer_client():
    code, data = PortainerInterface().auth()
    assert code == StatusCodes.OK
    return ClientApi(PORTAINER_URL, additional_headers={API_AUTH_HEADER: data['jwt']})


class PortainerInterface:
    class StackStatus:
        ACTIVE = 1
        INACTIVE = 2

    class ContainerState:
        RUNNING = 'running'
        EXITED = 'exited'
        CREATED = 'created'

    class CntLabel:
        BRANCH = 'cicd.branch'
        COMMIT = 'cicd.commit'
        VERSION = 'cicd.version'
        SERVICE_NAME = 'com.docker.swarm.service.name'

    @property
    def client(self):
        return get_portainer_client()

    def auth(self, user=PORTAINER_USER, password=PORTAINER_PASSWORD):
        uri = f"/api/auth"
        body = {
            "Username": user,
            "Password": password
        }
        query_params = {}
        return ClientApi(PORTAINER_URL).post(uri, body, query_params)

    @ttl_cache(ttl=PORTAINER_TTL_CACHE)
    def get_stacks(self):
        uri = '/api/endpoints'
        body = {}
        query_params = {}
        with reporter.supress_stdout():
            return self.client.get(uri, body, query_params)

    @ttl_cache(ttl=PORTAINER_TTL_CACHE)
    def get_containers_by_stack(self, stack_id, all=1):
        uri = f"/api/endpoints/{stack_id}/docker/containers/json"
        body = {}
        query_params = {'all': all}
        with reporter.supress_stdout():
            return self.client.get(uri, body, query_params)

    def retrieve_container_info(self, stack_id, container_id):
        uri = f"/api/endpoints/{stack_id}/docker/containers/{container_id}/json"
        body = {}
        query_params = {}
        # with reporter.supress_stdout():
        return self.client.get(uri, body, query_params)


    @ttl_cache(ttl=PORTAINER_TTL_CACHE)
    def get_active_env_infos(self):
        code, portainer_stacks = self.get_stacks()
        if code != StatusCodes.OK:
            raise RuntimeError(f"Expect code {StatusCodes.OK}, but receive {code}")
        result = []
        for stack in portainer_stacks:
            if stack['Status'] == self.StackStatus.INACTIVE:
                continue
            name = stack['Name']
            if 'legacy connection' in name.lower():
                continue
            scope = ServiceScope.find(name)
            env = Environment.find(name)
            if not all([scope, env]):
                continue
            result.append(EnvInfo(scope, env, str(stack['Id']), name))
        return result

    def get_interested_env_info(self, service_scope, env) -> List[EnvInfo]:
        envs = self.get_active_env_infos()
        envs = [
            i for i in envs
            if (i.scope == service_scope or service_scope == ServiceScope.ALL)
               and (i.env == env or env == Environment.ALL)
        ]
        return envs

    def get_containers(self, env_obj, container_name, status=ContainerState.RUNNING):
        code, containers = self.get_containers_by_stack(env_obj.id)
        assert code == StatusCodes.OK
        containers = [i for i in containers if i.get('State') == status]
        containers = [i for i in containers if [k for k in i.get('Names', []) if container_name in k]]
        return containers


def get_service_credentials_from_portainer(scope_name, env, container_name, login_variable, password_variable):
    portainer = PortainerInterface()
    envs = portainer.get_interested_env_info(scope_name, env)
    assert len(envs) == 1
    env_info = envs[0]
    containers = portainer.get_containers(env_info, container_name)
    assert len(containers) == 1
    container_id = containers[0].get('Id')
    assert container_id
    code, container = portainer.retrieve_container_info(env_info.id, container_id)
    assert code == StatusCodes.OK

    user = password = ''
    container_envs = getter('Config.Env', container, [])
    container_envs = dict(i.split('=') for i in container_envs)
    if login_variable:
        assert login_variable in container_envs
        user = container_envs[login_variable]

    if password_variable:
        assert password_variable in container_envs
        password = container_envs[password_variable]

    return user, password

if __name__ == '__main__':
    client = PortainerInterface()
    keks = client.get_interested_env_info('coinmena', 'develop')
    code, data = client.get_containers(keks[0], 'coinmena_develop_pgbouncer')
    print(data)
