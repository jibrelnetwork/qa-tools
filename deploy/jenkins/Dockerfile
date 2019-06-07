FROM jenkinsci/blueocean
ENV JENKINS_USER_ID=1005
USER root

RUN echo http://dl-cdn.alpinelinux.org/alpine/edge/main >> /etc/apk/repositories

RUN apk update -U && \
    apk upgrade && \
    apk add --no-cache g++ python3=3.7.3-r0 python3-dev=3.7.3-r0 libffi-dev make openssl-dev clang musl-dev postgresql-dev

RUN python3 -m pip install --upgrade pip

RUN pip3 install docker-compose

RUN mkdir -p /app
COPY ./requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

RUN echo http://dl-2.alpinelinux.org/alpine/edge/community/ >> /etc/apk/repositories
RUN apk --no-cache add shadow && usermod -u ${JENKINS_USER_ID} jenkins

USER jenkins
