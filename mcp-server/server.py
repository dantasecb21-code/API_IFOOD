# API_IFOOD MCP Server - ULTRA-STABLE V4 (Final Fix)
import os
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

# --- Early Logging ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
logger.info("📡 BOOTING UP...")

load_dotenv()

# TOKEN PARA O LOVABLE: ifood2026
MASTER_KEY = "ifood2026"

# --- Integrations (Lazy) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip("'").strip('"')

supabase_client = None

def get_db():
    global supabase_client
    if supabase_client is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase Enabled.")
        except Exception as e:
            logger.error(f"❌ Supabase failed: {e}")
    return supabase_client

# --- MCP Tooling ---
mcp = Server("api-ifood-integrator")

@mcp.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_today_kpis",
            description="Returns delivery KPIs (volume, conversion) for today.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="system_check",
            description="Checks internal connectivity.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    db = get_db()
    
    if name == "system_check":
        return [TextContent(type="text", text=f"Status: Online. DB Connection: {'OK' if db else 'Fail'}")]
    
    if name == "get_today_kpis":
        if not db: return [TextContent(type="text", text="Error: DB not connected.")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = db.table("pedidos").select("id").gte("created_at", f"{hoje}T00:00:00").execute()
            return [TextContent(type="text", text=f"Total orders for {hoje}: {len(res.data or [])}")]
        except Exception as e:
            return [TextContent(type="text", text=f"DB Error: {str(e)}")]
            
    return [TextContent(type="text", text="Tool not found.")]

# --- FastAPI Setup ---
app = FastAPI()

# CORS for Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "OK", "v": "4.0.0"}

@app.get("/")
async def root():
    return {"message": "MCP Server Active. Use /mcp for tools."}

# Security
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

# MCP Transport Configuration
transport = FastapiServerTransport(mcp, endpoint="/mcp")

@app.post("/mcp")
async def mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def mcp_sse(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info("� READY TO RECEIVE TRAFFIC.")
    uvicorn.run(app, host="0.0.0.0", port=port)
