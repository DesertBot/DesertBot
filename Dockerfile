FROM python:3.10-slim AS base

FROM base AS build

RUN apt-get update && \
    apt-get install -y \
    build-essential \
	cargo \
    cmake \
    cython3 \
    git \
    libre2-dev \
    ninja-build \
    pybind11-dev \
    python3-dev \
	rustc

ENV CXXFLAGS="-std=c++14"

COPY requirements.txt /

RUN pip install --no-cache-dir Cython && \
    pip install --no-cache-dir -r /requirements.txt

WORKDIR /app

COPY . /app

RUN git remote set-url origin git@github.com:DesertBot/DesertBot.git

# Comment out these 6 lines if you want !update to work with requirements.txt updates
# The image will be larger to support this
#FROM base
#RUN apt-get update && apt-get install -y libre2-3
#RUN apt-get install -y git
#COPY --from=build /usr/local /usr/local
#COPY --from=build /app /app
#WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-u", "start.py"]

CMD ["-h"]
