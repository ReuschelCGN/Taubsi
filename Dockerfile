# Basic Docker image for Taubsi

FROM python:3.8.10

RUN export DEBIAN_FRONTEND=noninteractive && apt-get update \
&& apt-get install -y --no-install-recommends
RUN mkdir /usr/src/app
WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/Rapptz/discord.py.git@45d498c1b76deaf3b394d17ccf56112fa691d160
ENV PYTHONUNBUFFERED 1
COPY . /usr/src/app/
