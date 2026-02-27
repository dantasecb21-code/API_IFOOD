FROM python:3.11-slim

WORKDIR /app

# Copia os requisitos usando o caminho relativo à raiz do projeto
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o conteúdo da pasta mcp-server para o diretório de trabalho /app
COPY mcp-server/ .

EXPOSE 8000

CMD ["python", "server.py"]

