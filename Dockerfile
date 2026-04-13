FROM python:3.11-slim

# gcc + python3-dev needed to compile asyncpg and pgvector C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Shell form required — $PORT is injected by Railway at runtime and must be shell-expanded
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
