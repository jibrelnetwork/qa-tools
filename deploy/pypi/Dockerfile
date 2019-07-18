FROM codekoala/pypi

RUN apk update \
    && apk add python3 \
    && apk add postgresql-dev gcc python3-dev musl-dev make

RUN python3 -m pip install --upgrade pip \
    && pip3 install wheel

COPY ./deploy/pypi/update_package.sh /
COPY . /app/

ENTRYPOINT ["/entrypoint.sh"]
