import allure
import pytest
import logging


class Reporter(object):

    PNG = allure.attachment_type.PNG
    JSON = allure.attachment_type.JSON
    TEXT = allure.attachment_type.TEXT
    HTML = allure.attachment_type.HTML

    def step(self, step_text, step_prefix=None):
        if step_prefix is None:
            step_prefix = 'Step'
        logging.info(step_prefix + f": {step_text}")
        return allure.step(step_text)

    def attach(self, title, body, type_=TEXT):
        body = str(body)
        return allure.attach(body, title, type_)

    def parametrize(self, *args, **kwargs):
        return pytest.mark.parametrize(*args, **kwargs)

    def skip_test(self, msg):
        return pytest.mark.skip(msg)

    def skipif_test(self, reason, msg):
        return pytest.mark.skip(bool(reason), msg)


reporter = Reporter()
