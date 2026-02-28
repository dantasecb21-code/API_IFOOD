# API_IFOOD MCP Server - FINAL STABILITY V8
import os
import sys
import logging
from datetime import datetime

# --- FORCE LOGGING TO STDOUT ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mcp-server")
logger.info("� [V8] STARTING ENGINE...")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API_IFOOD MCP Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# KEY FIXA: ifood2026
MASTER_KEY = "ifood2026"

@app.get("/health")
@app.get("/")
async def health_check():
    logger.info("💓 Health check hit.")
    return {
        "status": "OK",
        "version": "8.0.0",
        "env_port": os.getenv("PORT", "not set"),
        "time": datetime.utcnow().isoformat()
    }

# --- Lazy Loading Transport ---
_transport = None

async def get_transport():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            mcp_srv = Server("api-ifood-integrator")
            
            @mcp_srv.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_ifood_kpis", description="Busca KPIs no Supabase Externo", inputSchema={"type": "object"}),
                    Tool(name="ping", description="Testa a ponte", inputSchema={"type": "object"})
                ]
            
            @mcp_srv.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text=f"Servidor V8 respondendo ferramenta {name}.")]

            _transport = FastapiServerTransport(mcp_srv, endpoint="/mcp")
            logger.info("✅ MCP Transport Ready.")
        except Exception as e:
            logger.error(f"❌ MCP Init Error: {e}")
    return _transport

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    t = await get_transport()
    if not t: return JSONResponse(status_code=500, content={"error": "MCP Error"})
    return await t.handle_post_notification(request)

@app.get("/mcp")
async def handle_mcp_sse(request: Request):
    t = await get_transport()
    if not t: return JSONResponse(status_code=500, content={"error": "MCP Error"})
    return await t.handle_get_sse(request)

# Security
@app.middleware("http")
async def auth_gate(request: Request, call_next):
    # Pass public GET routes
    if request.method == "GET" and request.url.path in ["/health", "/", "/mcp", "/saúde"]:
        return await call_next(request)
    
    # Check Auth on POST
    if request.method == "POST" and request.url.path == "/mcp":
        auth_h = request.headers.get("Authorization")
        if not auth_h or auth_h != f"Bearer {MASTER_KEY}":
            logger.warning(f"Unauthorized access attempt to {request.url.path}")
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    # ESSENCIAL: Pegar a porta que o Railway injeta no ambiente!
    port_str = os.getenv("PORT", "8080")
    try:
        current_port = int(port_str)
    except ValueError:
        current_port = 8080
        
    logger.info(f"� BINDING TO PORT {current_port}")
    uvicorn.run(app, host="0.0.0.0", port=current_port, log_level="info")
