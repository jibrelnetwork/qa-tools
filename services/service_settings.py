import os
from distutils.util import strtobool

# SLACK_PORT = os.getenv("SLACK_PORT", '45455')
SLACK_OBJ_TTL = int(os.getenv("SLACK_OBJ_TTL", 300))
SLACK_TO_PORTAINER_HOOK_TIMEOUT = int(os.getenv("SLACK_TO_PORTAINER_HOOK_TIMEOUT", 60))
SLACK_TOKEN = os.getenv("SLACK_TOKEN", '')
SLACK_FOLDER_CONFIG = os.getenv('SLACK_FOLDER_CONFIG', '.')

PORTAINER_URL = os.getenv("PORTAINER_URL", 'https://portainer-dev.jdev.network')
PORTAINER_USER = os.getenv("PORTAINER_USER", '')
PORTAINER_PASSWORD = os.getenv("PORTAINER_PASSWORD", '')
PORTAINER_TOKEN_LIFETIME = int(os.getenv("SLACK_OBJ_TTL", 300))
