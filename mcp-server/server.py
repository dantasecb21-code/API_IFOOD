# API_IFOOD MCP Server - INTELLIGENT BRIDGE (V5.0)
import os
import sys
import logging
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

load_dotenv()

# TOKEN: ifood2026
MASTER_KEY = "ifood2026"

# --- Supabase Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip("'").strip('"')

_db = None
def get_db():
    global _db
    if _db is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _db = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Connected to External Supabase.")
        except Exception as e:
            logger.error(f"❌ Supabase Connection Fail: {e}")
    return _db

# --- MCP Tooling ---
mcp = Server("api-ifood-integrator")

@mcp.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_ifood_kpis",
            description="Busca métricas de desempenho (vendas, conversão, cancelamentos) diretamente do Supabase externo.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="check_database_health",
            description="Verifica se a ponte entre o Railway e o Supabase está funcionando.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    db = get_db()
    
    if name == "check_database_health":
        status = "CONECTADO" if db else "DESCONECTADO"
        return [TextContent(type="text", text=f"Status da Ponte: {status}")]
    
    if name == "get_ifood_kpis":
        if not db: return [TextContent(type="text", text="Erro: Não foi possível conectar ao Supabase externo.")]
        try:
            # Tenta buscar pedidos de hoje
            hoje = datetime.utcnow().date().isoformat()
            # Tentamos na tabela pedidos ou ifood_pedidos
            res = db.table("pedidos").select("status").gte("created_at", f"{hoje}T00:00:00").execute()
            data = res.data or []
            total = len(data)
            concluidos = sum(1 for p in data if p.get("status") in ["concluido", "entregue"])
            
            msg = f"📊 Dados obtidos do Supabase Externo ({hoje}):\n"
            msg += f"- Total de Pedidos: {total}\n"
            msg += f"- Pedidos Concluídos: {concluidos}\n"
            msg += f"- Taxa de Sucesso: {round((concluidos/total*100),1) if total > 0 else 0}%"
            return [TextContent(type="text", text=msg)]
        except Exception as e:
            # Se a tabela 'pedidos' não existir, tentamos 'metricas_semanais'
            try:
                res = db.table("metricas_semanais").select("*").limit(1).order("created_at", desc=True).execute()
                if res.data:
                    return [TextContent(type="text", text=f"Métricas recentes encontradas: {res.data[0]}")]
            except:
                pass
            return [TextContent(type="text", text=f"Erro ao buscar KPIs: {str(e)}")]
            
    return [TextContent(type="text", text="Ferramenta não encontrada.")]

# --- FastAPI Implementation ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "OK", "bridge": "Active", "mcp_ready": mcp is not None}

# Transport
transport = FastapiServerTransport(mcp, endpoint="/mcp")

@app.post("/mcp")
async def mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def mcp_sse(request: Request):
    return await transport.handle_get_sse(request)

@app.middleware("http")
async def auth(request: Request, call_next):
    if request.url.path in ["/", "/health", "/mcp"] and request.method == "GET":
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    auth_h = request.headers.get("Authorization")
    if request.method == "POST" and request.url.path == "/mcp":
        if not auth_h or auth_h != "Bearer ifood2026":
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
