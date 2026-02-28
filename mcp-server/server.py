# API_IFOOD MCP Server - V11 Hyper-Resilient
import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- Startup Logging ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
logger.info("🚩 V11 BOOTING...")

load_dotenv()

app = FastAPI()

# Permissive CORS for Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MASTER_KEY = "ifood2026"

# --- Simple Health Routes ---
@app.get("/health")
@app.get("/")
async def health():
    logger.info("💓 Pulsing...")
    return {"status": "OK", "v": "11.0", "time": datetime.utcnow().isoformat()}

# --- SSE / MCP Bridge ---
# Lazy load inside the routes to prevent boot crashes
_transport = None

async def start_mcp():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood")
            @srv.list_tools()
            async def list_tools():
                return [Tool(name="check", description="Test tools", inputSchema={"type": "object"})]
            
            @srv.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text="Success")]
                
            _transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ MCP Ready.")
        except Exception as e:
            logger.error(f"❌ MCP Failure: {e}")
    return _transport

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await start_mcp()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP Error"})

@app.post("/mcp")
async def mcp_post(request: Request):
    # Auth Check
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {MASTER_KEY}":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        
    t = await start_mcp()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP Error"})

if __name__ == "__main__":
    import uvicorn
    # ESSENCIAL: Pegar a porta do Railway
    target_port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 ENGINE ONLINE ON PORT {target_port}")
    uvicorn.run(app, host="0.0.0.0", port=target_port)
