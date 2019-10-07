import os
from  distutils.util import strtobool

JIRA_URL = "https://jibrelnetwork.atlassian.net/"
JENKINS_JOB_BUILD_URL = os.getenv("BUILD_URL", '')
ALLURE_PROJECT_ID = os.getenv("ALLURE_PROJECT_ID", 4)
DISABLE_SCHEMA_VALIDATOR = strtobool(os.getenv("DISABLE_SCHEMA_VALIDATOR", False))
IS_LOCAL_START = strtobool(os.getenv("IS_LOCAL_START", False))

if DISABLE_SCHEMA_VALIDATOR:
    for _ in range(5):
        print('Now You disable schema validator!!!!!!!!   DANGER!!!!')
