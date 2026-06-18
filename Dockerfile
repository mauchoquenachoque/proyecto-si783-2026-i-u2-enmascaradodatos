FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar librerias runtime del sistema y dos2unix
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    freetds-common \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

RUN dos2unix scripts/render-start.sh
RUN chmod +x scripts/render-start.sh

EXPOSE 10000

CMD ["bash", "scripts/render-start.sh"]
