import json
import requests
from pathlib import Path
from requests.auth import HTTPBasicAuth
from cachetools.func import lru_cache, ttl_cache

from qa_tool.utils.common import ClientApi, StatusCodes
from qa_tool.settings import ALLURE_TOKEN, ALLURE_URL, ALLURE_PROJECT_ID


# https://gist.github.com/eroshenkoam/8bc73f81d6ad0401db876f4d89ac8de0

# # this ugly hack, will be removed in the future
# JWT_TOKEN=$(curl --request POST -sL \
#      --url "${ENDPOINT}/api/uaa/oauth/token" \
#      --user 'acme:acmesecret' \
#      --form 'grant_type=apitoken' \
#      --form 'scope=openid' \
#      --form "token=${USER_TOKEN}" \
#      | jq -r .access_token)


CURR_DIR = Path('/app').resolve() if Path('/app').is_dir() else Path(__file__).parent
ALLURE_TESTS = CURR_DIR / "allure_tests.json"

ALLURE_CACHE_LIMIT = 300


class AllureApi:

    def __init__(self):
        self._auth_info = None
        self.client = ClientApi(ALLURE_URL)
        self.basic_auth_user = 'acme'
        self.basic_auth_pass = 'acmesecret'

    @property
    def token(self):
        if self._auth_info is None:
            code, self._auth_info = self.get_token()
            assert code == StatusCodes.OK
        return self._auth_info['access_token']

    @ttl_cache(ttl=ALLURE_CACHE_LIMIT)
    def get_token(self):
        print('Get token for allure connection')
        uri = f"{ALLURE_URL}/api/uaa/oauth/token"
        body = {
           'scope': 'openid',
           'token': ALLURE_TOKEN,
           'grant_type': 'apitoken',
        }
        resp = requests.post(uri, body, json=True, auth=HTTPBasicAuth(self.basic_auth_user, self.basic_auth_pass))
        return resp.status_code, resp.json()

    def get_test_cases(self, projectId, size=None, page=None, sort=None, ):
        print(f'Get cases for project {projectId}')
        uri = f"{ALLURE_URL}/api/rs/testcasetree/leaf"
        query_params = {
            "projectId": projectId,
            "sort": sort,
            "page": page,
            "size": size,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        resp = requests.get(uri, query_params, json=True, headers=headers)
        return resp.status_code, resp.json()

    def _format_test_name(self, name):
        return name.split('[', 1)[0]

    @ttl_cache(ttl=ALLURE_CACHE_LIMIT)
    def get_test_cases_by_project(self, project_id):
        code, data = self.get_test_cases(project_id, 10000)
        assert code == StatusCodes.OK
        cases = data['content']
        return {self._format_test_name(i['name']): i['id'] for i in cases}

    def dump_test_cases(self):
        issues = self.get_test_cases_by_project(ALLURE_PROJECT_ID)
        ALLURE_TESTS.write_text(json.dumps(issues))

    @lru_cache()
    def get_dumped_test_cases_map(self):
        try:
            test_mapping = json.loads(ALLURE_TESTS.read_text())
            return test_mapping
        except Exception:
            return {}


allure_api = AllureApi()


if __name__ == '__main__':
    client = AllureApi()
    data = client.get_token()
    print(client.token)
    cases_map = client.get_test_cases_by_project(7)
    print(data)
