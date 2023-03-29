FROM python:3.10-slim

RUN apt update && apt install -y --no-install-recommends git

RUN git clone https://github.com/DesertBot/weercd.git

ENTRYPOINT ["python", "weercd/weercd.py"]
