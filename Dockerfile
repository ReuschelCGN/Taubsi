# Basic Docker image for Taubsi

FROM python:3.8.10

RUN export DEBIAN_FRONTEND=noninteractive && apt-get update \
&& apt-get install -y --no-install-recommends
RUN mkdir /usr/src/app
WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/Rapptz/discord.py.git
ENV PYTHONUNBUFFERED 1
COPY . /usr/src/app/
