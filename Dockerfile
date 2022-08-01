# This file is intended to be used apart from the containing source code tree.

FROM python:3-alpine

# Version of Radicale (e.g. v3)
ARG VERSION=master
# Persistent storage for data
COPY radicale ./radicale
COPY radicale3-auth-ldap ./radicale3-auth-ldap
COPY config ./config
COPY requirements.txt ./requirements.txt
COPY main.py ./main.py

# TCP port of Radicale
EXPOSE 5232

RUN apk add --no-cache ca-certificates openssl \
 && apk add --no-cache --virtual .build-deps gcc libffi-dev musl-dev \
    && pip install "./radicale3-auth-ldap"

RUN pip3 install -r requirements.txt

CMD ["python", "main.py", "--config", "./config", "--debug"]
