import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

# Log imediato na porta de comando
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp")

# Pega a porta EXATA do Railway (o segredo do sucesso)
PORT = int(os.environ.get("PORT", 8080))
logger.info(f"🚩 [V23] TENTANDO LIGAR NA PORTA {PORT}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MCP (CRIAÇÃO SOB DEMANDA) ---
mcp_srv = Server("api-ifood-v23")
_t = None

@mcp_srv.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [Tool(name="ping", description="Verificar ponte", inputSchema={"type":"object"})]

@mcp_srv.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    return [TextContent(type="text", text="✅ Ponte V23 está Viva!")]

def get_t():
    global _t
    if _t is None:
        _t = FastapiServerTransport(mcp_srv, endpoint="/mcp")
    return _t

# --- ROTAS DE SAÚDE (RESPONDE EM < 1MS) ---
@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "v": "V23-QUICK-PING"}

@app.get("/mcp")
async def mcp_get(request: Request):
    return await get_t().handle_get_sse(request)

@app.post("/mcp")
async def mcp_post(request: Request):
    return await get_t().handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    # ESSA É A LINHA QUE O RAILWAY PRECISA VER:
    logger.info(f"🚀 Motores ligados em 0.0.0.0:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
