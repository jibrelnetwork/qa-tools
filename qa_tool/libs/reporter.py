import allure
import pytest
import logging

from qa_tool.settings import JIRA_URL
from qa_tool.libs.jira_integrate import get_autotest_issues, issue_is_open


def get_known_issues(token):
    issues = [issue for issue in get_autotest_issues() if token in issue.description]
    return issues


class Reporter(object):

    PNG = allure.attachment_type.PNG
    JSON = allure.attachment_type.JSON
    TEXT = allure.attachment_type.TEXT
    HTML = allure.attachment_type.HTML

    def step(self, step_text, step_prefix=None):
        if step_prefix is None:
            step_prefix = 'Step'
        msg = step_prefix + f": {step_text}"
        logging.info(msg)
        print(msg)
        return allure.step(msg)

    def attach(self, title, body, type_=TEXT):
        body = str(body)
        return allure.attach(body, title, type_)

    def parametrize(self, *args, **kwargs):
        return pytest.mark.parametrize(*args, **kwargs)

    @property
    def scenario(self):
        """dependencies for classes tests"""
        return pytest.mark.incremental

    def jira_issue_is_open(self, issue):
        return issue_is_open(issue)

    def skip_test(self, msg):
        return pytest.mark.skip(msg)

    def skipif_test(self, reason, msg):
        return pytest.mark.skip(bool(reason), msg)

    def simple_exception(self, is_exception=True):
        if is_exception:
            raise Exception('Some exception generated from action layer')
        else:
            assert 1 == 2

    def label(self, name, value):
        return allure.label(name, value)

    def jira_label(self, issue_id):
        return self.label('jira', issue_id)

    def _get_issue_url(self, issue):
        return f"{JIRA_URL}browse/{issue}", issue

    def dynamic_issue(self, issue):
        allure.dynamic.issue(*self._get_issue_url(issue))


reporter = Reporter()
