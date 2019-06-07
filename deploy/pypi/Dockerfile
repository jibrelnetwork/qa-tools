FROM codekoala/pypi

RUN apk update \
    && apk add python3 \
    && apk add postgresql-dev gcc python3-dev musl-dev

RUN python3 -m pip install --upgrade pip
RUN pip3 install wheel

COPY ./deploy/pypi/update_package.sh /
COPY . /app/
RUN chmod 770 /update_package.sh

ENTRYPOINT ["/entrypoint.sh"]
