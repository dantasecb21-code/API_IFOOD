FROM python:3.11-slim

WORKDIR /app

# Instale dependências de sistema se necessário
RUN apt-get update && apt-get install -x -y curl && rm -rf /var/lib/apt/lists/*

# Copie apenas o básico para o build de dependências ser rápido
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie o código fonte agora
COPY . .

# Expomos a porta do Railway
EXPOSE 8080

# Comando de Inicialização: 
# Rodamos o Guardian (que é instantâneo) enquanto o MCP carrega suas bibliotecas pesadas.
# IMPORTANTE: No Railway, o Guardian responderá /health para manter verde e o MCP rodará /mcp
CMD ["python", "server.py"]
