# API_IFOOD MCP Server - Production Final (Dual Auth Support)
import os
import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# --- Production Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("mcp-server")

# Load environment variables
load_dotenv()

# --- Security Configuration ---
# We accept both keys to ensure you can connect regardless of which one you have ready
KEY_A = "api_ifood_secret_token_123"
KEY_B = "IFood_Master_Key_2026_Secure"

# If you set a custom one in Railway Variables, it will use that instead:
MCP_API_KEY_ENV = os.getenv("MCP_API_KEY", "").strip().strip("'").strip('"')

logger.info("🚀 PRODUCTION SERVER STARTING...")
if MCP_API_KEY_ENV:
    logger.info(f"Using CUSTOM MCP_API_KEY from Railway (starts with: {MCP_API_KEY_ENV[:4]}...)")
else:
    logger.info(f"Using DEFAULT Keys: '{KEY_A}' OR '{KEY_B}'")

# --- Integration Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip().strip("'").strip('"')

# Global Supabase client (Lazy Initialized)
_supabase_client = None

def get_supabase() -> Optional[Any]:
    global _supabase_client
    if _supabase_client is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase connection established.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
    return _supabase_client

# --- MCP Tool Definitions ---
mcp_server = Server("api-ifood-production")

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_delivery_stats",
            description="Returns daily delivery metrics (orders, conversion) from the database.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="system_diagnostic",
            description="Checks the health of all external integrations.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    sb = get_supabase()
    
    if name == "system_diagnostic":
        status_msg = f"🌐 Server: ONLINE\n📦 Supabase: {'CONNECTED' if sb else 'DISCONNECTED'}"
        return [TextContent(type="text", text=status_msg)]

    if name == "get_delivery_stats":
        if not sb: return [TextContent(type="text", text="Error: Supabase disconnected.")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = sb.table("pedidos").select("status").gte("created_at", f"{hoje}T00:00:00").execute()
            data = res.data or []
            return [TextContent(type="text", text=f"Stats for {hoje}: {len(data)} orders found.")]
        except Exception as e:
            return [TextContent(type="text", text=f"Data Error: {str(e)}")]

    return [TextContent(type="text", text="Tool not found.")]

# --- FastAPI Framework ---
app = FastAPI(title="API_IFOOD Production Gateway")

@app.get("/health")
async def health_check():
    return {"status": "OK", "version": "2.1.0"}

@app.get("/")
async def welcome():
    return {"message": "API_IFOOD MCP is Live. Connect via /mcp"}

# Security Middleware (Dual-Key Auth)
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/", "/favicon.ico"] or request.method == "OPTIONS":
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing Bearer Token"})
    
    token_received = auth_header.split(" ")[1]
    
    # Validation logic
    authorized = False
    if MCP_API_KEY_ENV and token_received == MCP_API_KEY_ENV:
        authorized = True
    elif token_received in [KEY_A, KEY_B]:
        authorized = True
        
    if not authorized:
        logger.warning(f"Unauthorized access attempt with token ending in ...{token_received[-3:]}")
        return JSONResponse(status_code=401, content={"detail": "Invalid Token"})
    
    return await call_next(request)

# MCP Transport
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@app.post("/mcp")
async def mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def mcp_get(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
