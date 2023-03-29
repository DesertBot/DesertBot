FROM python:3.10-slim

RUN pip install pillow

RUN mkdir -p /app
WORKDIR /app
