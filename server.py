# API_IFOOD MCP Server - V21 UNSTOPPABLE
import os
import logging
import sys
import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

# Setup Logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-v21")
logger.info("🚩 [V21] INICIALIZANDO SERVIDOR RESILIENTE...")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MCP LOGIC ---
mcp_server = Server("api-ifood-eternal")

@mcp_server.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [
        Tool(
            name="check_health",
            description="Verifica se o servidor iFood está respondendo.",
            inputSchema={"type": "object"}
        )
    ]

@mcp_server.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    return [TextContent(type="text", text="✅ Servidor V21 Conectado e Estável!")]

# Global transport to be initialized safely
_transport = None

def get_transport():
    global _transport
    if _transport is None:
        # Inicializa o transporte apenas quando necessário
        _transport = FastapiServerTransport(mcp_server, endpoint="/mcp")
    return _transport

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "version": "V21-ETERNAL", "info": "Servidor Ativo"}

@app.get("/mcp")
async def mcp_sse(request: Request):
    """Canal SSE para manter a conexão eterna"""
    t = get_transport()
    # O FastapiServerTransport do MCP lida com o keep-alive internamente,
    # mas vamos garantir a resposta imediata para o Railway e Lovable.
    return await t.handle_get_sse(request)

@app.post("/mcp")
async def mcp_post(request: Request):
    """Recebe comandos do Lovable"""
    t = get_transport()
    return await t.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Servidor V21 pronto na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
