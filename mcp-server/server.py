# API_IFOOD MCP Server - FAST STARTUP VERSION
import os
import sys
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
logger.info("📡 ENGINE STARTING...")

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

# Aceitamos as duas versões por segurança
@app.get("/health")
@app.get("/saúde")
async def health():
    return {"status": "OK", "msg": "Ready"}

@app.get("/")
async def root():
    return {"status": "Online"}

# Carregamento preguiçoso do MCP
mcp_transport = None

async def get_transport():
    global mcp_transport
    if mcp_transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("ifood-server")
            
            @srv.list_tools()
            async def list_tools():
                return [Tool(name="check", description="Check DB", inputSchema={"type": "object"})]
                
            @srv.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text="OK")]
                
            mcp_transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ MCP Loaded lazily.")
        except Exception as e:
            logger.error(f"❌ MCP Load Error: {e}")
    return mcp_transport

@app.post("/mcp")
async def mcp_post(request: Request):
    t = await get_transport()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP Error"})

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_transport()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP Error"})

# Senha: ifood2026
@app.middleware("http")
async def auth_gate(request: Request, call_next):
    if request.url.path in ["/", "/health", "/saúde", "/mcp"] and request.method == "GET":
        return await call_next(request)
    
    auth = request.headers.get("Authorization")
    if request.method != "OPTIONS" and request.url.path == "/mcp" and request.method == "POST":
        if not auth or auth != "Bearer ifood2026":
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Uvicorn binding to port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
