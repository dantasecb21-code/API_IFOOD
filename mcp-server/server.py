# API_IFOOD MCP Server - Robust Version
import os
import asyncio
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport
from mcp.types import Tool, TextContent
from dotenv import load_dotenv
import httpx
from github import Github
from supabase import create_client, Client

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")
logger.info("Initializing API_IFOOD MCP Server...")

# Load environment variables
load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
IFOOD_CLIENT_ID = os.getenv("IFOOD_CLIENT_ID")
IFOOD_CLIENT_SECRET = os.getenv("IFOOD_CLIENT_SECRET")
IFOOD_BASE_URL = os.getenv("IFOOD_API_BASE_URL", "https://merchant-api.ifood.com.br")
MCP_API_KEY = os.getenv("MCP_API_KEY", "api_ifood_secret_token_123")

# Initialize GitHub Clients safely
GITHUB_TOKENS = os.getenv("GITHUB_TOKENS", "").split(",")
GITHUB_CLIENTS = []
for token in GITHUB_TOKENS:
    t = token.strip()
    if t and t not in ["your_token_1", "your_token_2", "your_github_token_1"]:
        try:
            GITHUB_CLIENTS.append(Github(t))
        except Exception as e:
            logger.error(f"Error initializing GitHub client: {e}")

# Initialize Supabase safely
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY and "your_supabase" not in SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase client initialized.")
    except Exception as e:
        logger.error(f"❌ Error initializing Supabase: {e}")

# --- MCP Logic ---
mcp_app = Server("api-ifood-integrator")

@mcp_app.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_daily_kpis",
            description="Calcula e retorna os KPIs de delivery do dia atual",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="github_global_search",
            description="Pesquisa issues em todos os repositórios GitHub vinculados",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Termo de pesquisa"}
                },
                "required": ["query"]
            }
        )
    ]

@mcp_app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "get_daily_kpis":
        if not supabase:
            return [TextContent(type="text", text="Erro: Supabase não conectado.")]
        
        hoje = datetime.utcnow().date()
        inicio = f"{hoje}T00:00:00"
        try:
            res = supabase.table("pedidos").select("status").gte("created_at", inicio).execute()
            total = len(res.data or [])
            return [TextContent(type="text", text=f"Total de pedidos hoje: {total}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Erro ao buscar KPIs: {e}")]

    elif name == "github_global_search":
        query = arguments.get("query", "")
        results = []
        for client in GITHUB_CLIENTS:
            try:
                issues = client.search_issues(query)
                for issue in issues[:3]:
                    results.append(f"- {issue.repository.full_name}: {issue.title}")
            except: continue
        return [TextContent(type="text", text="\n".join(results) or "Nenhum resultado.")]
    
    raise ValueError(f"Ferramenta desconhecida: {name}")

# --- FastAPI Setup ---
app = FastAPI(title="API_IFOOD MCP Server")

# Healthcheck endpoint - NO AUTH
@app.get("/health")
async def health():
    return {
        "status": "OK",
        "up": True,
        "supabase": supabase is not None,
        "github_accounts": len(GITHUB_CLIENTS)
    }

# Auth Middleware
@app.middleware("http")
async def verify_auth(request: Request, call_next):
    # Permite healthcheck e OPTIONS sem token
    if request.url.path in ["/health", "/"] or request.method == "OPTIONS":
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header.split(" ")[1] != MCP_API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    return await call_next(request)

# Mount MCP on /mcp
transport = FastapiServerTransport(mcp_app, endpoint="/mcp")

@app.post("/mcp")
async def handle_mcp(request: Request):
    return await transport.handle_post_notification(request) if request.method == "POST" else None

# Para o Railway/FastAPI mount tradicional
@app.get("/mcp")
async def handle_mcp_get(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Iniciando servidor MCP na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
