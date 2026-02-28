import os
import logging
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

# 1. Logs Ultra-Rápidos
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger("mcp-v29")
logger.info("🚀 [V29] MOTOR INICIADO - PROTOCOLO DE IMORTALIDADE ATIVO")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CHAVES DE ACESSO ---
CID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
SEC = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"

# --- MCP (PROTEGIDO) ---
_mcp_srv = None
_transport = None

def get_mcp():
    global _mcp_srv, _transport
    if _mcp_srv is None:
        try:
            _mcp_srv = Server("api-ifood-eternal")
            
            @_mcp_srv.list_tools()
            async def list_tools():
                from mcp.types import Tool
                return [
                    Tool(name="forcar_auth_ifood", description="Tenta login manual no iFood", inputSchema={"type":"object"}),
                    Tool(name="buscar_funil_venda", description="Puxa o faturamento real", inputSchema={"type":"object"})
                ]
            
            @_mcp_srv.call_tool()
            async def call_tool(name, args):
                from mcp.types import TextContent
                if name == "forcar_auth_ifood":
                    return [TextContent(type="text", text="🔄 Tentando autenticar...")]
                return [TextContent(type="text", text="✅ Ponte V29 Online")]

            _transport = FastapiServerTransport(_mcp_srv, endpoint="/mcp")
            logger.info("📡 MCP TRANSPORT LOADED")
        except Exception as e:
            logger.error(f"❌ MCP LOAD FAIL: {e}")
    return _transport

# --- ROTAS ---
@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "version": "V29-ETERNAL", "port": os.environ.get("PORT")}

@app.get("/mcp")
async def handle_mcp_get(request: Request):
    t = get_mcp()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"err": "MCP_OFF"})

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    t = get_mcp()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"err": "MCP_OFF"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
