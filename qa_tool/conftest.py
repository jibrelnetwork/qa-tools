import pytest
from allure_pytest.listener import AllureListener


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item
    outcome = yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_teardown(item):
    yield
    plugin = [i for i in item.config.pluginmanager.get_plugins() if isinstance(i, AllureListener)]
    if len(plugin) == 1:
        plugin = plugin[0]
        uuid = plugin._cache.get(item.nodeid)
        labels = plugin.allure_logger.get_test(uuid).labels
        labels_names = [i.name for i in labels]
        if 'subSuite' in labels_names:
            sub_index = labels_names.index('subSuite')
            labels[labels_names.index('suite')].value = labels[sub_index].value
            labels.pop(sub_index)


def pytest_runtest_setup(item):
    import qa_tool.override_conftest
    previousfailed = getattr(item.parent, "_previousfailed", None)
    if previousfailed is not None:
        pytest.xfail("previous test failed (%s)" % previousfailed.name)
