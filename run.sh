#!/bin/sh -e

if [[ "${QA_CUSTOM_COMMAND}" ]]; then
  echo "${QA_CUSTOM_COMMAND} $*"
  ${QA_CUSTOM_COMMAND}
  exit 0
fi

PYTEST_DEFAULT="pytest --execution-timeout ${TEST_TIMEOUT} --setup-timeout 10 --teardown-timeout 10 ${PYTEST_STOUT} --alluredir=${ALLURE_DIR}"


if [[ "$*" ]]; then
  echo "${PYTEST_DEFAULT} $*"
  ${PYTEST_DEFAULT} $*
else
  echo "${PYTEST_DEFAULT} -n ${TEST_THREAD_COUNT} ${TESTS_DIR}"
  ${PYTEST_DEFAULT} -n ${TEST_THREAD_COUNT} ${TESTS_DIR}
fi
