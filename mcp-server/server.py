# API_IFOOD MCP Server - ABSOLUTE RESILIENCE V9
import os
import sys
import logging
from datetime import datetime

# Configure logging at the very top
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("mcp-server")
logger.info("🚩 [V9] ENGINE BOOT SEQUENCE STARTING...")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API_IFOOD MCP V9")

# Permissive CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# KEY: ifood2026
MASTER_KEY = "ifood2026"

# --- BULLETPROOF HEALTH PATHS ---
@app.get("/health")
@app.get("/saúde")
@app.get("/saude")
@app.get("/")
async def health_check():
    logger.info("✅ Health/Root probe received.")
    return {
        "status": "OK", 
        "version": "9.0.0", 
        "msg": "The train has arrived at the station!",
        "port": os.getenv("PORT", "8080")
    }

# --- Lazy MCP Logic ---
_transport = None

async def get_transport():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood-integrator")
            
            @srv.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_ifood_stats", description="Busca métricas no Supabase Externo", inputSchema={"type": "object"}),
                    Tool(name="check_internal_status", description="Verifica integridade do servidor", inputSchema={"type": "object"})
                ]
            
            @srv.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text=f"Servidor V9 (Bridge) respondendo a {name}.")]

            _transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ MCP Transport Initialized.")
        except Exception as e:
            logger.error(f"❌ MCP Init Failed: {e}")
    return _transport

@app.post("/mcp")
async def mcp_post(request: Request):
    t = await get_transport()
    if not t: return JSONResponse(status_code=500, content={"error": "MCP Library Error"})
    return await t.handle_post_notification(request)

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_transport()
    if not t: return JSONResponse(status_code=500, content={"error": "MCP Library Error"})
    return await t.handle_get_sse(request)

# Security Middleware (Permissive for Health)
@app.middleware("http")
async def security_gate(request: Request, call_next):
    path = request.url.path
    method = request.method
    
    # Public GET paths
    if method == "GET" and path in ["/", "/health", "/saúde", "/saude", "/mcp"]:
        return await call_next(request)
    
    # OPTIONS for CORS
    if method == "OPTIONS":
        return await call_next(request)
        
    # Secure POST paths
    if method == "POST" and path == "/mcp":
        auth = request.headers.get("Authorization")
        if not auth or auth != f"Bearer {MASTER_KEY}":
            logger.warning(f"BLOCKED: Unauthorized POST to {path} from {request.client}")
            return JSONResponse(status_code=401, content={"detail": "Unauthorized. Use 'ifood2026'."})
            
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    # Capture Railway's dynamic PORT
    port_env = os.getenv("PORT", "8080")
    try:
        bind_port = int(port_env)
    except:
        bind_port = 8080
        
    logger.info(f"🚀 [V9] BINDING TO PORT: {bind_port}")
    uvicorn.run(app, host="0.0.0.0", port=bind_port, log_level="info")
