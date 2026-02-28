FROM python:3.11-slim

WORKDIR /app

# Instala curl para logs e testes
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia dependências
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do servidor
COPY mcp-server/ .

# Railway fornece a porta via variável $PORT.
# Usamos o formato de string para que o shell resolva a variável $PORT.
CMD uvicorn server:app --host 0.0.0.0 --port $PORT
