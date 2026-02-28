FROM python:3.11-slim

WORKDIR /app

# Instala apenas o essencial sem firulas
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Cache de dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fonte
COPY . .

# Railway usa a porta 8080 por padrão
ENV PORT=8080
EXPOSE 8080

# Inicialização direta do servidor MCP
CMD ["python", "mcp-server/server.py"]
