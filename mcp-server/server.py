# API_IFOOD MCP Server - DEFINITIVE STABLE VERSION
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

# --- Security ---
# USAR ESTA CHAVE NO LOVABLE: ifood2026
MCP_API_KEY = "ifood2026"

# --- Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip("'").strip('"')

# Global Supabase client (Lazy Initialized)
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

# --- MCP Tools ---
mcp_app = Server("api-ifood-integrator")

@mcp_app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_delivery_kpis",
            description="Busca KPIs de vendas e conversão do dia atual",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="check_system",
            description="Verifica se o servidor está conseguindo falar com o banco de dados",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "check_system":
        sb = get_supabase()
        return [TextContent(type="text", text=f"Sistema Online. Banco de Dados: {'Conectado' if sb else 'Desconectado'}")]
    
    if name == "get_delivery_kpis":
        sb = get_supabase()
        if not sb: return [TextContent(type="text", text="Erro: Banco de dados não configurado.")]
        try:
            hoje = datetime.utcnow().date().isoformat()
            res = sb.table("pedidos").select("status").gte("created_at", f"{hoje}T00:00:00").execute()
            count = len(res.data or [])
            return [TextContent(type="text", text=f"📊 Status em {hoje}: {count} pedidos registrados.")]
        except Exception as e:
            return [TextContent(type="text", text=f"Erro ao buscar dados: {str(e)}")]
            
    return [TextContent(type="text", text="Ferramenta não encontrada.")]

# --- FastAPI ---
app = FastAPI(title="API_IFOOD MCP Final")

@app.get("/health")
async def health():
    return {"status": "OK", "version": "3.0.0"}

@app.get("/")
async def root():
    return {"message": "Server is ONLINE. Use /mcp with Bearer Token 'ifood2026'"}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/", "/favicon.ico"] or request.method == "OPTIONS":
        return await call_next(request)
    
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {MCP_API_KEY}":
        logger.warning("Acesso negado: Token incorreto")
        return JSONResponse(status_code=401, content={"detail": "Unauthorized - Use token 'ifood2026'"})
    
    return await call_next(request)

# MCP Transport
transport = FastapiServerTransport(mcp_app, endpoint="/mcp")

@app.post("/mcp")
async def handle_mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def handle_mcp_sse(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"📡 SERVIDOR INICIADO NA PORTA {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
