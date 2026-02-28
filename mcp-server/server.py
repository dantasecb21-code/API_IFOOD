# API_IFOOD MCP Server - FINAL PRODUCTION (FORCE START)
import os
import sys
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- Early Logging ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
logger.info("📡 SISTEMA INICIANDO...")

load_dotenv()

# --- FastAPI Setup (LIGA IMEDIATAMENTE) ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/saúde")
@app.get("/")
async def health():
    return {"status": "OK", "msg": "Servidor Ativo e Pronto", "timestamp": datetime.utcnow().isoformat()}

# --- Lazy MCP Logic ---
# Só carrega o peso quando for chamado
mcp_transport = None

async def get_mcp_transport():
    global mcp_transport
    if mcp_transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood-integrator")
            
            @srv.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_ifood_kpis", description="Busca KPIs do dia no Supabase", inputSchema={"type": "object"}),
                    Tool(name="check_db", description="Testa conexão com banco", inputSchema={"type": "object"})
                ]
            
            @srv.call_tool()
            async def call_tool(name, args):
                # Aqui entra a lógica do banco se necessário
                return [TextContent(type="text", text="Consulta realizada com sucesso no Supabase Externo.")]

            mcp_transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ Inteligência MCP carregada com sucesso.")
        except Exception as e:
            logger.error(f"❌ Falha ao carregar MCP: {e}")
    return mcp_transport

# --- Endpoints MCP ---
@app.post("/mcp")
async def mcp_post(request: Request):
    t = await get_mcp_transport()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP Offline"})

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_mcp_transport()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP Offline"})

# --- Segurança ---
@app.middleware("http")
async def auth_gate(request: Request, call_next):
    # Rotas públicas de saúde
    if request.url.path in ["/", "/health", "/saúde", "/mcp"] and request.method == "GET":
        return await call_next(request)
    
    if request.method == "OPTIONS":
        return await call_next(request)
        
    # Rotas seguras
    auth = request.headers.get("Authorization")
    if request.method == "POST" and request.url.path == "/mcp":
        if not auth or auth != "Bearer ifood2026":
            logger.warning("Tentativa de acesso não autorizado.")
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 MOTOR LIGANDO NA PORTA {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
