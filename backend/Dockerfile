FROM python:3.11.2-slim

ARG UID
ARG GID

ENV DEBIAN_FRONTEND="noninteractive"

RUN groupadd -g $GID python && \
    useradd -g python -u $UID -m -d /app -s /bin/bash python

RUN python3.11 -m pip --no-cache-dir install --upgrade pip \
                                                       gunicorn

USER $UID

ENV PATH=$PATH:~/.local/bin

WORKDIR /app

COPY --chown=$UID:$GID ./requirements.txt ./requirements.txt

RUN python3.11 -m pip --no-cache install -r ./requirements.txt

COPY --chown=$UID:$GID . .
