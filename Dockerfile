FROM python:3.10.9-bullseye AS Thatkitebot

WORKDIR /app/

COPY ./requirements.txt /tmp/requirements.txt
COPY ./thatkitebot /app/thatkitebot


WORKDIR /tmp/

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y python3-dev gcc libfreeimage3 libwebp-dev libjpeg-turbo-progs git libffi-dev

RUN python3 -m venv /venv

RUN /venv/bin/pip3 install --upgrade pip

RUN /venv/bin/pip3 install -r requirements.txt

WORKDIR /app/
