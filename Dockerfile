FROM python:3.11-slim

WORKDIR /app

# Instala curl para diagnósticos
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia e instala requisitos
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY mcp-server/ .

# Railway fornece a porta via $PORT. Nosso server.py já lê isso.
ENV PORT=8080
EXPOSE 8080

# Início direto via Python para capturar a porta do ambiente
CMD ["python", "server.py"]
