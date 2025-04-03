FROM python:3.12.9-bookworm AS thatkitebot

# install system package dependencies
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3-dev gcc libfreeimage3 libwebp-dev libjpeg-turbo-progs git libffi-dev units imagemagick

# create venv
RUN python3 -m venv /app/thatkitebot-venv/
RUN /app/thatkitebot-venv/bin/pip3 install --upgrade pip Cython
RUN /app/thatkitebot-venv/bin/pip3 install setuptools

# download and install patched version of si-prefix
WORKDIR /tmp/
RUN git clone https://github.com/ThatRedKite/si-prefix.git 
WORKDIR /tmp/si-prefix
RUN /app/thatkitebot-venv/bin/python setup.py build
RUN /app/thatkitebot-venv/bin/python setup.py install

#build the pcb calculator module
COPY ./src/pcb_mod/ /tmp/pcb_mod/
WORKDIR /tmp/pcb_mod/
RUN /app/thatkitebot-venv/bin/python setup.py build
RUN /app/thatkitebot-venv/bin/python setup.py install

WORKDIR /app/

# copy the bot stuff 
COPY ./requirements.txt /tmp/requirements.txt
COPY ./thatkitebot /app/thatkitebot

# install python package dependencies
RUN /app/thatkitebot-venv/bin/pip3 install -r /tmp/requirements.txt
