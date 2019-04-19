FROM jenkinsci/blueocean

USER root

RUN apk update \
    && apk add py-pip \
    && pip install docker-compose

RUN echo http://dl-2.alpinelinux.org/alpine/edge/community/ >> /etc/apk/repositories
RUN apk --no-cache add shadow && usermod -u 1005 jenkins

USER jenkins