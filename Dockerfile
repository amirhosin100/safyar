FROM docker.arvancloud.ir/python:3.13

ENV PYTHONUNBUFFERED=1

WORKDIR /src

COPY ./requirements.txt ./
RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . /src
