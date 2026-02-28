FROM python:3.11-slim

WORKDIR /app

# Instala dependências básicas
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY mcp-server/ .

# Railway usa a porta 8080. Uvicorn vai ler de $PORT se usarmos a flag --port.
ENV PORT=8080
EXPOSE 8080

# Comando padrão de produção usando uvicorn diretamente
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
