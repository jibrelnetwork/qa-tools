import re
import hashlib

import pytest
from cachetools.func import lru_cache
from allure_pytest.listener import AllureListener

from qa_tool.settings import IS_LOCAL_START, JIRA_URL
from qa_tool.libs.reporter import get_known_issues
from qa_tool.libs.jira_integrate import TEST_TOKEN_PREFIX, jira, dump_jira_issues, attach_known_issues_and_check_pending


@lru_cache()
def get_hash(text):
    only_words = "".join(re.findall("[a-z]{3,}", text))
    return f"{TEST_TOKEN_PREFIX}_{hashlib.md5(only_words.encode()).hexdigest()}"


@lru_cache()
def tokenize_text(token, text):
    def hook(*args, **kwargs):
        return "%s\n%s" % (text, token)

    return hook


def get_allure_plugin(item):
    plugin = [i for i in item.config.pluginmanager.get_plugins() if isinstance(i, AllureListener)]
    if len(plugin) == 1:
        return plugin[0]


def get_allure_test(item):
    plugin = get_allure_plugin(item)
    uuid = plugin._cache.get(item.nodeid)
    return plugin.allure_logger.get_test(uuid)


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionstart(session):
    import qa_tool.override_conftest
    try:
        if IS_LOCAL_START:
            dump_jira_issues()
    finally:
        print("Can't dump jira issue with autotests token")
    yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item
    token = None
    if call.excinfo:
        plugin = get_allure_plugin(item)
        try:
            path = item.nodeid.split('/tests/')[-1]
            token = get_hash(path + call.excinfo.exconly())
            plugin.add_label('autotest_token', (token,))
        except Exception as e:
            print(e)
            outcome = yield
            return
        known_issues = get_known_issues(token)
        auto_token_getter = tokenize_text(token, call.excinfo.exconly())
        jira_new_issue_link = jira.get_jira_created_issue_url(item.nodeid, auto_token_getter())
        docsting = item._obj.__doc__
        if docsting:
            description = "\n".join(("[create bug](%s)" % jira_new_issue_link, docsting))
        else:
            description = "[create bug](%s)" % jira_new_issue_link
        plugin.add_description(description)
        call.excinfo.exconly = auto_token_getter

    outcome = yield

    if token and known_issues:
        is_pending = attach_known_issues_and_check_pending(known_issues)
        if not is_pending:
            return
        report = outcome.get_result()
        plugin.add_label('jira_bug_link', (f"{JIRA_URL}browse/{i.id}" for i in known_issues))
        def hook():
            setattr(report, "outcome", "skipped")
            setattr(report, "wasxfail", "known issue")
            return report

        outcome.get_result = hook


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_teardown(item):
    yield
    labels = get_allure_test(item).labels
    labels_names = [i.name for i in labels]
    if 'subSuite' in labels_names:
        sub_index = labels_names.index('subSuite')
        labels[labels_names.index('suite')].value = labels[sub_index].value
        labels.pop(sub_index)


def pytest_runtest_setup(item):
    previousfailed = getattr(item.parent, "_previousfailed", None)
    if previousfailed is not None:
        pytest.xfail("previous test failed (%s)" % previousfailed.name)
