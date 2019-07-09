import os
import sys
import pytest


pytest.register_assert_rewrite('qa_tool.utils.common')
pytest.register_assert_rewrite('qa_tool.utils.api_helper')
pytest.register_assert_rewrite('qa_tool.libs.reporter')


def run_test(file_name, capture_stdout=True, allure_dir=None):
    cmd = [
        file_name, "-vvv",
    ]

    if capture_stdout:
        cmd.append("-s")

    test_name = os.path.splitext(os.path.basename(file_name))[0]
    alluredir = os.path.normpath("%s/%s/" % (allure_dir or "allure-results", test_name))
    cmd.extend(["--alluredir", alluredir])
    print(cmd)
    sys.exit(pytest.main(cmd))
