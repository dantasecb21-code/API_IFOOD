# API_IFOOD MCP Server - Ultra-Robust Version (Railway Fix)
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
import httpx

# --- Early Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("mcp-server")
logger.info("🚀 STARTING API_IFOOD MCP SERVER...")

# Load env vars
load_dotenv()

def clean_env(key: str, default: str = None) -> str:
    val = os.getenv(key, default)
    if val:
        # Remove any surrounding quotes that might have been pasted in Railway
        return val.strip().strip("'").strip('"')
    return val

# --- Configuration with cleaning ---
SUPABASE_URL = clean_env("SUPABASE_URL")
SUPABASE_KEY = clean_env("SUPABASE_KEY")
IFOOD_CLIENT_ID = clean_env("IFOOD_CLIENT_ID")
IFOOD_CLIENT_SECRET = clean_env("IFOOD_CLIENT_SECRET")
MCP_API_KEY = clean_env("MCP_API_KEY", "api_ifood_secret_token_123")

logger.info(f"Config Loaded: Supabase URL: {SUPABASE_URL}")
logger.info(f"Config Loaded: MCP Key: {'Set' if MCP_API_KEY else 'Missing'}")

# Delayed imports to avoid startup crashes
try:
    from github import Github
    from supabase import create_client, Client
    logger.info("✅ Core libraries imported successfully.")
except ImportError as e:
    logger.error(f"❌ Critical Import Error: {e}")
    # We continue so healthcheck can still pass and show us this error

# Initialize Clients safely
supabase: Optional[Any] = None
GITHUB_CLIENTS = []

def init_clients():
    global supabase, GITHUB_CLIENTS
    
    # Supabase Init
    if SUPABASE_URL and SUPABASE_KEY and "your_" not in SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase initialized.")
        except Exception as e:
            logger.error(f"❌ Supabase init failed: {e}")
    else:
        logger.warning("⚠️ Supabase credentials missing/placeholder.")

    # GitHub Init
    tokens = clean_env("GITHUB_TOKENS", "").split(",")
    for t in tokens:
        token = t.strip()
        if token and "your_" not in token:
            try:
                GITHUB_CLIENTS.append(Github(token))
                logger.info("✅ GitHub account linked.")
            except Exception as e:
                logger.error(f"❌ GitHub init failed: {e}")

# Run init
init_clients()

# --- MCP Tooling ---
mcp_server = Server("api-ifood-integrator")

@mcp_server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_daily_kpis",
            description="Returns daily delivery KPIs (Conversion, Orders)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="check_status",
            description="Check the MCP Server internal connectivity status",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "check_status":
        status = f"Supabase: {'Connected' if supabase else 'Disconnected'}\nGitHub Accounts: {len(GITHUB_CLIENTS)}"
        return [TextContent(type="text", text=status)]
    
    if name == "get_daily_kpis":
        if not supabase:
            return [TextContent(type="text", text="Error: Supabase is not connected.")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            # Simple count for health check
            res = supabase.table("pedidos").select("id", count="exact").gte("created_at", f"{hoje}T00:00:00").execute()
            count = res.count if hasattr(res, 'count') else len(res.data or [])
            return [TextContent(type="text", text=f"Orders today: {count}")]
        except Exception as e:
            return [TextContent(type="text", text=f"KPI Error: {str(e)}")]
            
    return [TextContent(type="text", text="Unknown tool")]

# --- FastAPI App ---
app = FastAPI(title="API_IFOOD MCP Server")

# Healthcheck MUST BE FIRST AND NO AUTH
@app.get("/health")
async def health():
    logger.info("Healthcheck requested")
    return {
        "status": "OK", 
        "info": "api_ifood_mcp",
        "connections": {
            "supabase": supabase is not None,
            "github": len(GITHUB_CLIENTS)
        }
    }

@app.get("/")
async def root():
    return {"message": "API_IFOOD MCP Server is running. Use /mcp for SSE or POST."}

# Middleware for Auth
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Allow health and root
    if request.url.path in ["/health", "/", "/favicon.ico"] or request.method == "OPTIONS":
        return await call_next(request)
    
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer ") or auth.split(" ")[1] != MCP_API_KEY:
        logger.warning(f"Unauthorized access attempt to {request.url.path}")
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    return await call_next(request)

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
    # Use PORT from Railway or default to 8080 (some platforms prefer it over 8000)
    port = int(os.getenv("PORT", 8080))
    logger.info(f"� SERVER STARTING ON PORT {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
