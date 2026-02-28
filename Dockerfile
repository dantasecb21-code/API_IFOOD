FROM python:3.11-slim

WORKDIR /app

# Instala curl para healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências usando o caminho correto da pasta
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o conteúdo da pasta mcp-server para a raiz do container
COPY mcp-server/ .

# Railway usa a porta 8080
ENV PORT=8080
EXPOSE 8080

# Inicia o servidor (agora o server.py está na raiz da pasta /app no container)
CMD ["python", "server.py"]
