FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Comando profissional do Uvicorn para Railway
CMD uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info
