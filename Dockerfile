FROM pypy:bullseye
COPY requirements.txt /tkb/requirements.txt

WORKDIR /tkb/

RUN apt-get update

RUN apt-get install -y pypy-wand python3-numpy gcc libfreeimage3 libwebp-dev libjpeg-turbo-progs

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

