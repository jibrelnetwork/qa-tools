FROM python:3.7-alpine

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

WORKDIR /app

ENTRYPOINT ["pytest", "--execution-timeout", "600", "-vvv", "-s", "--alluredir=./allure-results/"]
CMD ["-n", "10", "./tests"]                                                                                                                                                                                                  14,0-1        All