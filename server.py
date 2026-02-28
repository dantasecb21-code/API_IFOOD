import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configuração de Logs básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

app = FastAPI()

# Permite que o Lovable se conecte sem problemas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/")
async def health():
    logger.info("💓 Healthcheck recebido e respondido!")
    return {"status": "OK", "message": "Estou vivo e funcionando!"}

@app.get("/mcp")
async def mcp_status():
    return {"status": "MCP pronto para configuração"}

if __name__ == "__main__":
    import uvicorn
    # Forçamos a porta 8080 que é a padrão do Railway
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Iniciando servidor na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
