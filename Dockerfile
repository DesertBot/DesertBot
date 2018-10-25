FROM python:3.6-alpine AS base

FROM base AS build
RUN apk --update add \
    build-base \
    git \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    linux-headers \
    musl-dev \
    openssl-dev \
    re2-dev
WORKDIR /app
RUN git clone --depth 1 https://github.com/DesertBot/DesertBot.git /app
RUN pip install --no-cache-dir Cython && \
    pip install --no-cache-dir -r requirements.txt

# Uncomment these 5 lines for an even smaller image
# You'll lose the ability to do live requirements updates, though
#FROM base
#RUN apk --update add git libffi libxml2 libxslt musl openssl re2
#COPY --from=build /usr/local /usr/local
#COPY --from=build /app /app
#WORKDIR /app

ARG config
ENV config=$config PYTHONUNBUFFERED=1
ENTRYPOINT python -u start.py -c $config
