import os
import logging
import sys
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

# 1. Configurar Logging Imediato
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-v20")
logger.info("🚩 V20: PROTOCOLO OFICIAL SENDO INICIADO...")

app = FastAPI()

# 2. CORS Total (Inquebrável para o Lovable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Inicializar o Servidor MCP (Top Level para ser Rápido)
mcp_server = Server("api-ifood-bridge")

@mcp_server.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [
        Tool(
            name="verificar_ponte",
            description="Verifica se o servidor iFood no Railway está respondendo.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    return [TextContent(type="text", text="✅ Sucesso! O Lovable está oficialmente conectado ao seu motor iFood V20.")]

# 4. Transporte SSE Oficial
# O segredo é que o 'mcp' cuida do roteamento SSE automaticamente aqui
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "info": "V20 - PROTOCOLO CORRIGIDO"}

@app.get("/mcp")
async def handle_get(request: Request):
    """Esta rota abre o túnel de comunicação que o Lovable precisa"""
    return await transport.handle_get_sse(request)

@app.post("/mcp")
async def handle_post(request: Request):
    """Esta rota recebe os comandos e os envia pelo túnel"""
    return await transport.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    # Railway PORT dinâmica
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Motores ligados na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
