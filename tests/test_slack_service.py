import os

from consts.paths import QA_TEST_DATA_DIR
from libs import slack_bot
from qa_tool.utils.utils import generate_value
from services.slack_service import Commands

SLACK_MOCO_FOLDER = QA_TEST_DATA_DIR / 'slack'

def override_new(cls):
    cls._CHANNELS_FILE = generate_value(suffix='.json')
    cls._ENVIRONMENT_FILE = generate_value(suffix='.json')
    return object.__new__(cls)


Commands.__new__ = override_new


class TestSlackService:

    def setup(self):
        slack_bot.config_folder = QA_TEST_DATA_DIR / 'tmp'
        self.command = Commands()

    def test_subscribe(self):
        self.command.prepare_env_infos()
        channel = generate_value()
        self.command.subscribe_channel_to_environment(channel, 'all', 'dev')
        expected = {i: {channel} for i in self.command._get_envs_info_by('all', 'dev')}
        assert self.command.SUBSCRIBED_CHANNELS == expected


if __name__ == '__main__':
    from qa_tool import run_test
    run_test(__file__)
