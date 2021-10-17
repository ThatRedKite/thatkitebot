FROM pypy:bullseye

WORKDIR /app/

COPY ./requirements.txt /app/requirements.txt
COPY ./thatkitebot /app/thatkitebot


RUN apt-get update

RUN apt-get install -y pypy-wand python3-numpy gcc libfreeimage3 libwebp-dev libjpeg-turbo-progs git

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt


