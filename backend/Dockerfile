# Build from the repo root (the app reads SQL migrations from ../database):
#   docker build -f backend/Dockerfile -t scoreivy-backend .
FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ /app/backend/
COPY database/ /app/database/

RUN useradd --create-home app
USER app

EXPOSE 8000
# --proxy-headers makes rate limits use the real client IP behind the host's load balancer.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
