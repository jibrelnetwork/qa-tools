# QA tools

## Setup

* install docker
* install docker-compose
* pip install -r requirement.txt


### Environment variables

- `JIRA_NAME` - jira email
- `JIRA_PASSWORD` - jira cloud API key
- `IS_LOCAL_START` - **(bool)** disable download information from jira when you start any pytest format files
- `DISABLE_SCHEMA_VALIDATOR` - **(bool)** disable *validate_type_wrap* for api

Other environment variable you can find in qa_tool/settings.py

### Setup dockerfile

If you create test image from this base image for you access this environment variable for configure test start.
This configuration u can see in **run.sh**. Examples in **Dockerfile**

- ALLURE_DIR
- TESTS_DIR
- TEST_THREAD_COUNT
- TEST_TIMEOUT
- PYTEST_STOUT

Also for easy start use docker-compose. ``docker-compose run testing``
