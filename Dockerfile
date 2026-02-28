FROM python:3.11-slim

WORKDIR /app

# Instalação rápida
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Variáveis de ambiente para estabilidade
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Usamos sh -c para garantir que o $PORT seja lido corretamente
CMD ["sh", "-c", "python server.py"]
