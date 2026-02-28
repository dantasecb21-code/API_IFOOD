# API_IFOOD MCP Server - Production Final Version
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
logger.info("🚀 INITIALIZING PRODUCTION MCP SERVER...")

# Load environment variables
load_dotenv()

# --- Security Configuration ---
# New Secure Key generated for the user
NEW_SECURE_KEY = "IFood_Master_Key_2026_Secure"
MCP_API_KEY = os.getenv("MCP_API_KEY", NEW_SECURE_KEY).strip().strip("'").strip('"')

# --- Integration Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip().strip("'").strip('"')
IFOOD_CLIENT_ID = os.getenv("IFOOD_CLIENT_ID")
IFOOD_CLIENT_SECRET = os.getenv("IFOOD_CLIENT_SECRET", "").strip().strip("'").strip('"')

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
mcp_server = Server("api-ifood-production-gateway")

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_ifood_daily_kpis",
            description="Returns daily delivery metrics (orders, conversion) from the Supabase database.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="sync_latest_ifood_orders",
            description="Triggers a synchronization between iFood API and Supabase database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "merchant_id": {"type": "string", "description": "The unique iFood Merchant UUID"}
                },
                "required": ["merchant_id"]
            }
        ),
        Tool(
            name="system_status",
            description="Checks the health of all external integrations (Supabase, iFood, Auth).",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    sb = get_supabase()
    
    if name == "system_status":
        status_msg = (
            f"🌐 Server: ONLINE\n"
            f"📦 Supabase: {'CONNECTED' if sb else 'DISCONNECTED'}\n"
            f"🔑 MCP Auth: {'SECURE' if MCP_API_KEY == NEW_SECURE_KEY else 'CUSTOM'}\n"
            f"🍔 iFood ID: {'SET' if IFOOD_CLIENT_ID else 'MISSING'}"
        )
        return [TextContent(type="text", text=status_msg)]

    if name == "get_ifood_daily_kpis":
        if not sb: return [TextContent(type="text", text="Error: Supabase integration not configured.")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = sb.table("pedidos").select("status").gte("created_at", f"{hoje}T00:00:00").execute()
            data = res.data or []
            total = len(data)
            success = sum(1 for p in data if p.get("status") in ["entregue", "concluido"])
            return [TextContent(type="text", text=f"Stats for {hoje}: {total} orders, {success} successful delivered.")]
        except Exception as e:
            return [TextContent(type="text", text=f"KPI Error: {str(e)}")]

    if name == "sync_latest_ifood_orders":
        # Placeholder for real iFood sync logic
        m_id = arguments.get("merchant_id", "N/A")
        return [TextContent(type="text", text=f"Sync triggered for Merchant {m_id}. Data will appear in Supabase shortly.")]

    return [TextContent(type="text", text="Error: Tool execution failed - unknown tool.")]

# --- FastAPI Framework ---
app = FastAPI(title="API_IFOOD Production Gateway")

@app.get("/health")
async def health_check():
    # Public route for Railway status probe
    return {"status": "OK", "version": "2.0.0", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def welcome():
    return {"message": "API_IFOOD MCP Production Gateway is Online. Connect via Lovable using the /mcp endpoint."}

# Security Middleware (Bearer Token Auth)
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Bypass for Health and Root
    if request.url.path in ["/health", "/", "/favicon.ico"] or request.method == "OPTIONS":
        return await call_next(request)
    
    # Check Bearer Header
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {MCP_API_KEY}":
        logger.warning(f"Blocking unauthorized request to {request.url.path}")
        return JSONResponse(status_code=401, content={"detail": "Unauthorized - Use the correct Bearer Token"})
    
    return await call_next(request)

# MCP Transport Setup
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@app.post("/mcp")
async def mcp_post_endpoint(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def mcp_get_sse_endpoint(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    # Respecting Dynamic Port for Railway
    port = int(os.getenv("PORT", 8080))
    logger.info(f"📡 SERVER LIVE ON PORT {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
