FROM python:3.6-slim-stretch
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository ppa:nelhage/livegrep -y && apt-get install -y \
    build-essential \
    git \
    libre2-dev
RUN git clone https://github.com/DesertBot/DesertBot.git /app
WORKDIR /app
RUN pip install Cython
RUN pip install -r requirements.txt
ARG config
ENV config=$config
RUN echo "Config file: $config"
ENTRYPOINT python start.py -c $config
