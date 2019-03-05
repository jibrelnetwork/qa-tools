import os
import sys
import pytest


def run_test(file_name, capture_stdout=True):
    cmd = [
        file_name, "-vvv"
    ]

    if not capture_stdout:
        cmd.append("-s")

    test_name = os.path.splitext(os.path.basename(file_name))[0]
    alluredir = os.path.normpath("%s%s/" % ("allure-results/", test_name))
    cmd.extend(["--alluredir", alluredir])
    print(cmd)
    sys.exit(pytest.main(cmd))
