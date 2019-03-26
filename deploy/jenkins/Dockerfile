FROM jenkinsci/blueocean

USER root

RUN apk update \
    && apk add py-pip \
    && pip install docker-compose
#    && chmod 771 /usr/local/bin/docker-compose \
#    && chown root:999 /usr/local/bin/docker-compose

USER jenkins