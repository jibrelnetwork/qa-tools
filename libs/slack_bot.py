import json

import slack
from typing import List
from pathlib import Path
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

    def init_config(self, file_name):
        save_file_path = self.config_folder / file_name
        if not self.config_folder.exists():
            self.config_folder.mkdir(parents=True)
        if not save_file_path.exists():
            save_file_path.touch()
            save_file_path.write_text('{}')
            return None
        return json.loads(save_file_path.open().read())

    def save_config(self, file_name, data, model):
        save_file_path = self.config_folder / file_name
        serl_data = model().dumps(data)
        save_file_path.open('w').write(serl_data)

    @staticmethod
    def text(*msg):
        return {'text': '\n'.join(msg)}

    @staticmethod
    def dict_to_str(some_dict, msg=None):
        result = '\n'.join([f"{k}= {v}" for k, v in some_dict.items()])
        if msg:
            result = f"{msg}\n{result}"
        return result

    def get_field(self, title, value, short=True):
        return {
            'title': title,
            'value': value,
            'short': short,
        }

    def get_attachment(self, fields, color=None, ts=None, **kwargs):
        kwargs.update({
            'fields': fields,
            'color': color,
            'ts': ts,
        })
        return kwargs


slack_bot = SlackBot()
