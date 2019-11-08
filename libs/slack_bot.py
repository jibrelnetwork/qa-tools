import json

import slack
from pathlib import Path
from typing import List, Any
from collections import namedtuple
from cachetools.func import ttl_cache

from qa_tool.utils.common import StatusCodes
from qa_tool.utils.utils import classproperty
from services.service_settings import SLACK_TOKEN, SLACK_OBJ_TTL, SLACK_FOLDER_CONFIG


SlackChannel = namedtuple('SlackChannel', ['id', 'name'])


@ttl_cache(ttl=SLACK_OBJ_TTL)
def get_slack_bot():
    return slack.WebClient(token=SLACK_TOKEN)


class SlackBot:

    def __init__(self):
        self.config_folder = Path(SLACK_FOLDER_CONFIG)

    @classproperty
    def service(self) -> slack.WebClient:
        return get_slack_bot()

    @ttl_cache(ttl=SLACK_OBJ_TTL)
    def get_channels(self) -> List[SlackChannel]:
        resp = self.service.channels_list(exclude_archived=1)
        assert resp['ok']
        assert resp.status_code == StatusCodes.OK
        channels = resp.data['channels']
        return [SlackChannel(i.get('id'), i.get('name_normalized').lower()) for i in channels]

    def find_channel(self, channel_info):
        for i in self.get_channels():
            if channel_info in i:
                return i

    def init_config(self, file_name) -> Any(None, dict):
        save_file_path = self.config_folder / file_name
        try:
            if not save_file_path.exists():
                self.config_folder.mkdir(parents=True)
                self.save_config(file_name, {})
                return {}
            return json.loads(save_file_path.open().read())
        except Exception as e:
            print(f"Can't init {save_file_path.resolve()}\n{str(e)}")

    def save_config(self, file_name, data):
        save_file_path = self.config_folder / file_name
        try:
            save_file_path.open('w').write(json.dumps(data))
        except Exception as e:
            print(f"Can't save {save_file_path.resolve()}\n{str(e)}")

    @staticmethod
    def text(*msg):
        return {'text': '\n'.join(msg)}

    @staticmethod
    def dict_to_str(some_dict, msg=None):
        result = '\n'.join([f"{k}={v}" for k, v in some_dict.items()])
        if msg:
            result = f"{msg}\n{result}"
        return result

    def get_attachments(self, data):
        return


slack_bot = SlackBot()
