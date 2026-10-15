# Production image: the website plus a headless Chromium for PDF rendering.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY chartbook ./chartbook
COPY samples ./samples

# Orders and finished books live here; mount a persistent volume at /data.
VOLUME ["/data"]
EXPOSE 8000

# One worker: background book writing and the rate limiter live in this process.
# The host's load balancer sits in front, so trust its X-Forwarded-For header to see real visitor addresses.
CMD ["uvicorn", "chartbook.web.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
