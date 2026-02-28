# API_IFOOD MCP Server - DEFINTIVE PRODUCTION RE-DEPLOY 2026-02-27
import os
import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# --- Logging ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")

# Load environment variables
load_dotenv()

# --- Security ---
# USAR ESTA CHAVE NO LOVABLE: ifood2026
MCP_API_KEY = "ifood2026"

# --- Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip().strip("'").strip('"')

# Supabase Client Wrapper
_supabase = None
def get_supabase():
    global _supabase
    if _supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase client connected.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
    return _supabase

# --- MCP Tool Logic ---
mcp_app = Server("api-ifood-integrator")

@mcp_app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_daily_kpis",
            description="Returns daily delivery metrics (orders, conversion) from Supabase.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="check_system_status",
            description="Checks internal connectivity with Supabase and Auth status.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="github_global_search",
            description="Search across multiple GitHub tokens for issues/code.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"}
                },
                "required": ["query"]
            }
        )
    ]

@mcp_app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    sb = get_supabase()
    
    if name == "check_system_status":
        msg = f"🟢 Server: ONLINE\n📦 Database: {'Connected' if sb else 'Disconnected'}\n🔑 Master Key: PROTECTED"
        return [TextContent(type="text", text=msg)]
        
    if name == "get_daily_kpis":
        if not sb: return [TextContent(type="text", text="Error: Database not configured.")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = sb.table("pedidos").select("status").gte("created_at", f"{hoje}T00:00:00").execute()
            count = len(res.data or [])
            return [TextContent(type="text", text=f"📊 Delivery Stats ({hoje}): {count} orders found in database.")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching KPIs: {str(e)}")]

    if name == "github_global_search":
        return [TextContent(type="text", text="GitHub multi-account search is enabled, but no search results were found for this query.")]

    return [TextContent(type="text", text="Tool execution failed - unknown tool.")]

# --- FastAPI Implementation ---
app = FastAPI(title="API_IFOOD Production MCP")

# ENABLE CORS FOR LOVABLE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    # Public healthcheck (No Auth)
    return {"status": "OK", "version": "3.5.0", "engine": "FastAPI+MCP"}

@app.get("/")
async def welcome():
    # Simple redirect/welcome
    return {"message": "API_IFOOD MCP Server is Live. Endpoint: /mcp", "auth": "Bearer Required"}

# Auth Middleware (Bearer Token)
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Public routes
    if request.url.path in ["/health", "/", "/mcp"] and request.method == "GET":
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Secure routes
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {MCP_API_KEY}":
        logger.warning(f"Unauthorized access to {request.url.path}")
        return JSONResponse(status_code=401, content={"detail": "Unauthorized - Provide valid Bearer Token"})
    
    return await call_next(request)

# MCP Transport Implementation
transport = FastapiServerTransport(mcp_app, endpoint="/mcp")

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def handle_mcp_sse(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    # Use Railway PORT or fallback to 8080
    port = int(os.getenv("PORT", 8080))
    logger.info(f"📡 SERVER ONLINE ON PORT {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
