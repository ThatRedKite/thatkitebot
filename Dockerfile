FROM python:3.10-bullseye

WORKDIR /app/

COPY ./requirements.txt /tmp/requirements.txt
COPY ./thatkitebot /app/thatkitebot

WORKDIR /tmp/

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y python3-wand python3-numpy gcc libfreeimage3 libwebp-dev libjpeg-turbo-progs git

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

RUN git clone https://github.com/Pycord-Development/pycord --depth 1

WORKDIR /tmp/pycord/

RUN pip3 install -U .[speed]

WORKDIR /app/

