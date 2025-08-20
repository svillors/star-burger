FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ./star_burger ./star_burger
COPY ./assets ./assets
COPY ./templates ./templates
COPY ./foodcartapp ./foodcartapp
COPY ./geodata ./geodata
COPY ./restaurateur ./restaurateur
COPY ./manage.py ./manage.py

