FROM python:3.7-alpine

ENV ALLURE_DIR="./allure-results/" \
    TESTS_DIR="./tests" \
    TEST_THREAD_COUNT="10" \
    TEST_TIMEOUT="600" \
    PYTEST_STOUT="-vvv -s"

# build dependencies
RUN apk update \
    && apk add \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

COPY /requirements.txt /requirements-qa-tools.txt
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r /requirements-qa-tools.txt

COPY . /qa_tools/

WORKDIR /app

ENTRYPOINT ["/qa_tools/run.sh"]
CMD [""]                                                                                                                                                                                                  14,0-1        All