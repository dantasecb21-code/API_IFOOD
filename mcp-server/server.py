# API_IFOOD MCP Server - BULLETPROOF VERSION
import os
import sys
import logging

# --- Setup Logging ASAP ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
logger.info("📡 Starting engine...")

# --- Minimal FastAPI for Healthcheck ---
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "OK", "msg": "Guardian is alive"}

@app.get("/")
async def root():
    return {"status": "Online", "mode": "MCP Gateway"}

# --- Lazy MCP Imports ---
# Isso evita que o servidor caia se a lib mcp der erro no início
mcp_server = None
transport = None

def init_mcp():
    global mcp_server, transport
    try:
        from mcp.server import Server
        from mcp.server.fastapi import FastapiServerTransport
        from mcp.types import Tool, TextContent
        
        mcp_server = Server("ifood-prod-server")
        
        @mcp_server.list_tools()
        async def list_tools():
            return [Tool(name="check_status", description="Verify system", inputSchema={"type": "object"})]
            
        @mcp_server.call_tool()
        async def call_tool(name, args):
            return [TextContent(type="text", text="System is fully operational.")]
            
        transport = FastapiServerTransport(mcp_server, endpoint="/mcp")
        logger.info("✅ MCP Engine loaded successfully.")
    except Exception as e:
        logger.error(f"❌ MCP Engine failed to load: {e}")

# Chave: ifood2026
MASTER_KEY = "ifood2026"

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    if transport is None: init_mcp()
    if transport: return await transport.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP not loaded"})

@app.get("/mcp")
async def handle_mcp_sse(request: Request):
    if transport is None: init_mcp()
    if transport: return await transport.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP not loaded"})

@app.middleware("http")
async def auth_gate(request: Request, call_next):
    if request.url.path in ["/", "/health", "/mcp"] and request.method == "GET":
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {MASTER_KEY}":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    # Importante: Tentamos carregar o MCP antes de abrir o servidor
    init_mcp()
    logger.info(f"🚀 SERVER BINDING TO PORT {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
