# API_IFOOD MCP Server - V10 ABSOLUTE STABILITY
import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
logger.info("🚩 V10 Starting...")

app = FastAPI()

# Permissive CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# KEY: ifood2026
MASTER_KEY = "ifood2026"

# ALL POSSIBLE HEALTH PATHS (No Middleware for these)
@app.get("/health")
@app.get("/saúde")
@app.get("/saude")
@app.get("/")
async def health():
    return {"status": "OK", "v": "10.0.0", "msg": "Online"}

# --- Lazy MCP ---
_transport = None

async def get_transport():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood")
            
            @srv.list_tools()
            async def list_tools():
                return [Tool(name="get_kpis", description="Busca KPIs", inputSchema={"type": "object"})]
            
            @srv.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text="Dados retornados via Bridge MCP.")]

            _transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ MCP Loaded.")
        except Exception as e:
            logger.error(f"❌ MCP Error: {e}")
    return _transport

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_transport()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP Error"})

@app.post("/mcp")
async def mcp_post(request: Request):
    # Verificação manual básica para o endpoint MCP POST
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {MASTER_KEY}":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    t = await get_transport()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP Error"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
