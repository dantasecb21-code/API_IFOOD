# API_IFOOD MCP Server - SUPER ROBUST V7
import os
import logging
import sys
from datetime import datetime

# Configure logging immediately
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
logger.info("📡 ENGINE BOOTING...")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# KEY: ifood2026
MASTER_KEY = "ifood2026"

@app.get("/health")
@app.get("/saúde")
@app.get("/")
async def health():
    return {"status": "OK", "version": "7.0.0", "time": datetime.utcnow().isoformat()}

# --- MCP LOGIC (Lazy Loaded) ---
_mcp_transport = None

async def get_transport():
    global _mcp_transport
    if _mcp_transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood-integrator")
            
            @srv.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_ifood_kpis", description="Busca métricas no Supabase", inputSchema={"type": "object"}),
                    Tool(name="system_status", description="Verifica o status interno", inputSchema={"type": "object"})
                ]
            
            @srv.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text="Servidor respondendo via MCP Bridge.")]

            _mcp_transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ MCP Transport Initialized.")
        except Exception as e:
            logger.error(f"❌ MCP Initialization Failed: {e}")
    return _mcp_transport

@app.post("/mcp")
async def mcp_post(request: Request):
    t = await get_transport()
    if not t: return JSONResponse(status_code=500, content={"error": "MCP Error"})
    return await t.handle_post_notification(request)

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_transport()
    if not t: return JSONResponse(status_code=500, content={"error": "MCP Error"})
    return await t.handle_get_sse(request)

# Security Middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Pass health checks and SSE GET
    if request.url.path in ["/health", "/saúde", "/", "/mcp"] and request.method == "GET":
        return await call_next(request)
    
    # Check POST to /mcp
    if request.url.path == "/mcp" and request.method == "POST":
        auth = request.headers.get("Authorization")
        if not auth or auth != f"Bearer {MASTER_KEY}":
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
    return await call_next(request)

# If run directly (for local testing)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Starting Uvicorn on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
