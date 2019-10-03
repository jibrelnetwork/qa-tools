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

    def jira_issue(self, issue):
        allure.dynamic.issue("https://jibrelnetwork.atlassian.net/browse/" + issue)  # TODO: need fix link in tests
        if self.jira_issue_is_open(issue):
            return pytest.mark.skipif("True", reason="issue '%s' is open" % issue)
        else:
            return pytest.mark.skipif("False")

    def jira_issue_is_open(self, issue):
        from libs.jira_integrate import issue_is_open
        return issue_is_open(issue)

    def skip_test(self, msg):
        return pytest.mark.skip(msg)

    def skipif_test(self, reason, msg):
        return pytest.mark.skip(bool(reason), msg)


reporter = Reporter()
