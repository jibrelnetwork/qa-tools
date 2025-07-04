import os
from distutils.util import strtobool

JIRA_URL = "https://jibrelnetwork.atlassian.net/"
ALLURE_URL = "http://allure-server.jdev.network"
ALLURE_TOKEN = os.getenv("ALLURE_TOKEN", '')
JENKINS_JOB_BUILD_URL = os.getenv("BUILD_URL", '')
ALLURE_PROJECT_ID = int(os.getenv("ALLURE_PROJECT_ID", 4))
DISABLE_SCHEMA_VALIDATOR = strtobool(os.getenv("DISABLE_SCHEMA_VALIDATOR", 'False'))
IS_LOCAL_START = strtobool(os.getenv("IS_LOCAL_START", 'False'))
MAIN_APP_URL = os.getenv('API_CONN_STR') or os.getenv("BACKEND_API", 'http://127.0.0.1:9090')

ENV_NAME = os.getenv('ENV_NAME', 'develop').lower()  # consts/infrastructure.py -> Environment
ENV_SERVICE_SCOPE_NAME = os.getenv('ENV_SERVICE_SCOPE_NAME', '').lower()  # consts/infrastructure.py -> ServiceScope
SSH_PKEY_PATH = os.getenv('SSH_PKEY_PATH', '~/.ssh/id_rsa')
SSH_PKEY_PASSWORD = os.getenv('SSH_PKEY_PASSWORD', None)

if DISABLE_SCHEMA_VALIDATOR:
    for _ in range(5):
        print('Now You disable schema validator!!!!!!!!   DANGER!!!!')
