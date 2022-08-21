FROM python:3.10.6-bullseye

WORKDIR /app/

COPY ./requirements.txt /tmp/requirements.txt
COPY ./thatkitebot /app/thatkitebot

WORKDIR /tmp/

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y python3-numpy gcc libfreeimage3 libwebp-dev libjpeg-turbo-progs git

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

WORKDIR /app/

