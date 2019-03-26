FROM jenkinsci/blueocean:lts

USER root

RUN apt-get update \
    && apt-get install curl \
    && curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

USER jenkins

