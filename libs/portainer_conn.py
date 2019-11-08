from cachetools.func import ttl_cache

from qa_tool.utils.common import ClientApi
from services.service_settings import PORTAINER_TOKEN_LIFETIME, PORTAINER_USER, PORTAINER_PASSWORD, PORTAINER_URL


class PortainerCient(ClientApi):
    API_AUTH_HEADER = 'Authorization'

    @ttl_cache(ttl=PORTAINER_TOKEN_LIFETIME)
    def get_portainer_auth_token(self):
        return PortainerInterface.client.headers[self.API_AUTH_HEADER]

    def _update_header_from_cookies(self, resp):
        token = self.get_portainer_auth_token()
        if token != self.headers.get(self.API_AUTH_HEADER):
            self.headers.update({self.API_AUTH_HEADER: token})


class PortainerInterface:
    _client: PortainerCient = None

    def auth(self, user, password):
        uri = f"/email_info"
        body = {
            "Username": user,
            "Password": password
        }
        query_params = {}
        return self.client.post(uri, body, query_params)

    @property
    def client(self) -> PortainerCient:
        if self._client is None:
            self._client = PortainerCient(PORTAINER_URL)
            self.auth(PORTAINER_USER, PORTAINER_PASSWORD)
        return self._client

    def get_stacks(self):
        uri = '/api/endpoints'
        body = {}
        query_params = {}
        return self.client.get(uri, body, query_params)

    def get_containers_by_stack(self, stack_id, all=1):
        uri = f"/api/endpoints/{stack_id}/docker/containers/json"
        body = {}
        query_params = {'all': all}
        return self.client.get(uri, body, query_params)


if __name__ == '__main__':
    print(PortainerInterface().get_stacks())
