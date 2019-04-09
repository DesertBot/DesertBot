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
COPY requirements.txt /
RUN pip install --no-cache-dir Cython && \
    pip install --no-cache-dir -r /requirements.txt
WORKDIR /app
COPY . /app

# Comment out these 5 lines if you want !update to be able to do requirements.txt upgrades
# The image will be larger to support this
FROM base
RUN apk --update add git libffi libxml2 libxslt musl openssl re2
COPY --from=build /usr/local /usr/local
COPY --from=build /app /app
WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-u", "start.py"]

CMD ["-h"]
