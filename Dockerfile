FROM python:3.6-slim-stretch
WORKDIR /app
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:nelhage/livegrep -y && \
    apt-get install -y \
        build-essential \
        git \
        libre2-dev && \
    git clone https://github.com/DesertBot/DesertBot.git /app && \
    pip install Cython && \
    pip install -r requirements.txt
ARG config
ENV config=$config PYTHONUNBUFFERED=1
ENTRYPOINT python -u start.py -c $config
