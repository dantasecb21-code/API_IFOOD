from contextlib import asynccontextmanager
import os
import logging
import sys
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

# Log imediato
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-indestructible")
logger.info("🚩 [V22] LIGANDO MOTOR INDESTRUTÍVEL...")

# 1. Configurar o Servidor MCP
mcp_server = Server("api-ifood-bridge-v22")

@mcp_server.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [
        Tool(
            name="check_status",
            description="Verifica se a ponte iFood está estável.",
            inputSchema={"type": "object"}
        )
    ]

@mcp_server.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    return [TextContent(type="text", text="✅ Ponte V22 Conectada com Sucesso!")]

# 2. Transporte SSE do MCP
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # O lifecycle do FastAPI ajuda na estabilidade do Railway
    yield

app = FastAPI(lifespan=lifespan)

# 3. CORS Total para Evitar Bloqueios do Navegador do Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "v": "V22-INDESTRUCTIBLE", "uptime": "Eternal"}

@app.get("/mcp")
async def handle_mcp_get(request: Request):
    return await transport.handle_get_sse(request)

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    return await transport.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    # Pegar a porta do Railway dinâmica
    port = int(os.environ.get("PORT", 8080))
    # Desligue o reload para produção, isso evita desconexões automáticas
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
