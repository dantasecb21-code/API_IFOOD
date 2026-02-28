FROM python:3.11-slim

WORKDIR /app

# Instala curl e dependências de rede básicas
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Cache de dependências
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY mcp-server/ .

# Railway usa a variável $PORT. Nosso script server.py já lê essa variável.
ENV PORT=8080
EXPOSE 8080

# Inicia o servidor via Python para garantir que o bloco 'if name == main' rode 
# e capture a porta dinâmica do ambiente.
CMD ["python", "server.py"]
