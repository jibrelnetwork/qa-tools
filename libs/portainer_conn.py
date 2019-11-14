import os

from cachetools.func import ttl_cache

from qa_tool.libs.reporter import reporter
from qa_tool.utils.common import ClientApi, StatusCodes
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


if __name__ == '__main__':
    client = PortainerInterface()
    code, data = client.get_stacks()
    print(data)
