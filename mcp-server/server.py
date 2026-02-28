# API_IFOOD MCP Server - Final Production Fix (CORS & SSE)
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

# Load env
load_dotenv()

# --- Security ---
# CHAVE: ifood2026
MCP_API_KEY = "ifood2026"

# --- Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip("'").strip('"')

# Global Supabase client
_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase connected.")
        except Exception as e:
            logger.error(f"❌ Supabase error: {e}")
    return _supabase

# --- MCP Server Setup ---
mcp_server = Server("api-ifood-integrator")

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_delivery_kpis",
            description="Returns daily iFood metrics from the database",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="system_check",
            description="Checks internal connectivity",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    sb = get_supabase()
    if name == "system_check":
        return [TextContent(type="text", text=f"Online. Database: {'OK' if sb else 'Disconnected'}")]
    if name == "get_delivery_kpis":
        if not sb: return [TextContent(type="text", text="Error: DB not connected")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = sb.table("pedidos").select("id").gte("created_at", f"{hoje}T00:00:00").execute()
            return [TextContent(type="text", text=f"Found {len(res.data or [])} orders for {hoje}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    return [TextContent(type="text", text="Tool not found")]

# --- FastAPI Setup ---
app = FastAPI()

# VERY IMPORTANT: CORS for Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "OK", "version": "3.1.0"}

@app.get("/")
async def root():
    return {"message": "MCP Server Active"}

@app.middleware("http")
async def auth_check(request: Request, call_next):
    if request.url.path in ["/health", "/", "/mcp"] and request.method == "GET":
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {MCP_API_KEY}":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

# Correct MCP Transport Implementation
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    await transport.handle_post_notification(request)

@app.get("/mcp")
async def handle_mcp_sse(request: Request):
    async with transport.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
