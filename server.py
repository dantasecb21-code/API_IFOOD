import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Logging ultra-rápido
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-bridge")
logger.info("🚩 [V12] BOOT RÁPIDO INICIADO...")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variável para guardar o transporte e não carregar toda hora
_transport = None

async def get_mcp_transport():
    global _transport
    if _transport is None:
        try:
            # SÓ CARREGA AQUI DENTRO (Dá tempo do Railway ver que estamos vivos)
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood-integrator")
            
            @srv.list_tools()
            async def list_tools():
                return [Tool(name="testar_conexao", description="Verifica a saúde da ponte iFood", inputSchema={"type": "object"})]
            
            @srv.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text="✅ Ponte V12 Operacional!")]

            _transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ Inteligência MCP carregada em background.")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar MCP: {e}")
    return _transport

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "msg": "Servidor de Alta Disponibilidade Online"}

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_mcp_transport()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP Offline"})

@app.post("/mcp")
async def mcp_post(request: Request):
    t = await get_mcp_transport()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP Offline"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    # log_level warning para ser mais rápido
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
