# API_IFOOD MCP Server - NO-AUTH VERSION
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

# --- Logging ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")

# Load env
load_dotenv()

# --- Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip("'").strip('"')

# Deferred clients
supabase = None

def get_supabase():
    global supabase
    if supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase client initialized.")
        except Exception as e:
            logger.error(f"Supabase init error: {e}")
    return supabase

# --- MCP Tooling ---
mcp_server = Server("api-ifood-integrator")

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_daily_kpis", 
            description="Returns daily delivery KPIs from Supabase", 
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="check_status", 
            description="Checks if the server is connected to Supabase", 
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "check_status":
        sb = get_supabase()
        return [TextContent(type="text", text=f"Supabase Status: {'Connected' if sb else 'Disconnected'}")]
    
    if name == "get_daily_kpis":
        sb = get_supabase()
        if not sb: return [TextContent(type="text", text="Error: Supabase disconnected.")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = sb.table("pedidos").select("status").gte("created_at", f"{hoje}T00:00:00").execute()
            count = len(res.data or [])
            return [TextContent(type="text", text=f"Total orders for {hoje}: {count}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    return [TextContent(type="text", text="Tool not found")]

# --- FastAPI Setup ---
app = FastAPI(title="API_IFOOD MCP Server")

@app.get("/health")
async def health():
    return {"status": "OK", "auth": "OFF"}

@app.get("/")
async def root():
    return {"message": "Server is running WITHOUT AUTH for debugging."}

# NO MIDDLEWARE (PUBLIC ACCESS)
# This ensures Lovable can connect easily

# MCP Transport
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def handle_mcp_get(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
