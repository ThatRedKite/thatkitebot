FROM python:3.10.13-bookworm AS Thatkitebot

WORKDIR /app/

COPY ./requirements.txt /tmp/requirements.txt
COPY ./thatkitebot /app/thatkitebot

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y python3-dev gcc libfreeimage3 libwebp-dev libjpeg-turbo-progs git libffi-dev units

RUN python3 -m venv /app/thatkitebot-venv/

RUN /app/thatkitebot-venv/bin/pip3 install --upgrade pip

RUN /app/thatkitebot-venv/bin/pip3 install -r /tmp/requirements.txt

WORKDIR /app/
