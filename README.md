# QA tools

## Setup

* install docker
* install docker-compose
* pip install -r requirement.txt


### Environment variables

- `JIRA_NAME` - jira email
- `JIRA_PASSWORD` - jira cloud API key
- `IS_LOCAL_START` - *(bool)* disable download information from jira when you start any pytest format files
- `DISABLE_SCHEMA_VALIDATOR` - *(bool)* disable *validate_type_wrap* for api

Other environment variable you can find in qa_tool/settings.py
