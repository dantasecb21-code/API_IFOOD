# API_IFOOD MCP Server - Final Stable Version
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
MCP_API_KEY = os.getenv("MCP_API_KEY", "api_ifood_secret_token_123")

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
            description="Calcula e retorna os KPIs de delivery (vendas, conversão) do dia atual", 
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="check_internal_health", 
            description="Checa saúde interna das conexões com Supabase e iFood", 
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "check_internal_health":
        sb = get_supabase()
        msg = f"Supabase: {'OK' if sb else 'Erro/Desconectado'}\n"
        msg += f"MCP Key: {'Set' if MCP_API_KEY else 'Missing'}"
        return [TextContent(type="text", text=msg)]
    
    if name == "get_daily_kpis":
        sb = get_supabase()
        if not sb: 
            return [TextContent(type="text", text="Erro: Sem conexão com Supabase. Verifique as credenciais.")]
        
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = sb.table("pedidos").select("status").gte("created_at", f"{hoje}T00:00:00").execute()
            pedidos = res.data or []
            total = len(pedidos)
            aprovados = sum(1 for p in pedidos if p.get("status") in ["entregue", "concluido"])
            taxa = round((aprovados / total * 100), 2) if total > 0 else 0
            
            result_text = f"📊 KPIs de Hoje ({hoje}):\n- Total de Pedidos: {total}\n- Pedidos Aprovados: {aprovados}\n- Taxa de Conversão: {taxa}%"
            return [TextContent(type="text", text=result_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"Erro ao calcular KPIs: {str(e)}")]
    
    return [TextContent(type="text", text="Ferramenta não encontrada.")]

# --- FastAPI Setup ---
app = FastAPI(title="API_IFOOD MCP Server")

@app.get("/health")
async def health():
    # Rota simples para o Railway validar o deploy
    return {"status": "OK", "supabase_loaded": supabase is not None}

@app.get("/")
async def root():
    return {"message": "API_IFOOD MCP Server is active. Use /mcp for tools."}

# Middleware for Authentication
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for health and root
    if request.url.path in ["/health", "/", "/mcp"] and request.method == "GET":
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Check Bearer Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {MCP_API_KEY}":
        logger.warning("Unauthorized access attempt.")
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    return await call_next(request)

# MCP Transport Configuration
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def handle_mcp_get(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    # Use Railway PORT or fallback to 8080
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 SERVER STARTING ON PORT {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
