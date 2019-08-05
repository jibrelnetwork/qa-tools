#!/bin/sh -e


PYTEST_DEFAULT="pytest --execution-timeout ${TEST_TIMEOUT} ${PYTEST_STOUT} --alluredir=${ALLURE_DIR}"


if [[ "$*" ]]; then
  echo "${PYTEST_DEFAULT} $*"
  ${PYTEST_DEFAULT} $*
else
  echo "${PYTEST_DEFAULT} -n ${TEST_THREAD_COUNT} ${TESTS_DIR}"
  ${PYTEST_DEFAULT} -n ${TEST_THREAD_COUNT} ${TESTS_DIR}
fi
