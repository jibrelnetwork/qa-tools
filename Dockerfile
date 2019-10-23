FROM jenkins/jnlp-slave
USER root

RUN echo 'deb http://deb.debian.org/debian buster main' >> /etc/apt/sources.list

RUN apt update && apt install -y \
    python3 python3-pip

ENV ALLURE_DIR="./allure-results/" \
    TESTS_DIR="./tests" \
    TEST_THREAD_COUNT="10" \
    TEST_TIMEOUT="600" \
    PYTEST_STOUT="-vvv -s" \
    JIRA_PASSWORD='' \
    JIRA_USER=''

# build dependencies
RUN apt update \
    && apt install -y \
    gcc \
    musl-dev \
    libffi-dev

COPY /requirements.txt /requirements-qa-tools.txt
RUN pip3 install --no-cache-dir -r /requirements-qa-tools.txt

COPY . /qa_tools/
RUN pip3 install /qa_tools

USER jenkins

WORKDIR /app
RUN chmod 777 /app

#ENTRYPOINT ["/qa_tools/run.sh"]
#CMD [""]                                                                                                                                                                                                  14,0-1        All