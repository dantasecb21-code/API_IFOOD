import os
import logging
import sys
import asyncio
import httpx
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Configurações de Log Instantâneas
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("mcp-master")
logger.info("🚩 [V24] INICIANDO RESET TOTAL DO PROJETO...")

# Carregar ambiente (.env)
load_dotenv()

app = FastAPI(title="API_IFOOD Master Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MCP CORE (LAZY LOADING) ---
_transport = None

async def init_mcp_transport():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            from supabase import create_client
            
            srv = Server("api-ifood-master")
            
            @srv.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_ifood_overview", description="Vê faturamento e pedidos de hoje no banco.", inputSchema={"type": "object"}),
                    Tool(name="check_ifood_keys", description="Valida se o CLIENT_ID e SECRET do iFood estão ativos.", inputSchema={"type": "object"})
                ]
            
            @srv.call_tool()
            async def call_tool(name, args):
                # 1. Configuração do Banco
                url = os.getenv("SUPABASE_URL")
                key = os.getenv("SUPABASE_KEY")
                if not url or not key:
                    return [TextContent(type="text", text="❌ Erro: SUPABASE_URL ou KEY faltando no Railway.")]
                
                sb = create_client(url, key)
                
                if name == "get_ifood_overview":
                    # Busca as últimas métricas do iFood salvas no banco
                    res = sb.table("metricas_semanais").select("*").order("created_at", desc=True).limit(5).execute()
                    if res.data:
                        stats = "\n".join([f"📈 {m['created_at'][:16]} | R$ {m['vendas_valor']} | {m['quantidade_pedidos']} pedidos" for m in res.data])
                        return [TextContent(type="text", text=f"📊 Status do Funil de Vendas:\n{stats}")]
                    else:
                        return [TextContent(type="text", text="⚠️ Nenhuma métrica encontrada no banco jynlxtamjknauqhviaaq.")]

                if name == "check_ifood_keys":
                    # Tenta logar no iFood agora
                    c_id = os.getenv("IFOOD_CLIENT_ID")
                    c_sec = os.getenv("IFOOD_CLIENT_SECRET")
                    async with httpx.AsyncClient() as client:
                        auth_res = await client.post(
                            "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
                            data={"grantType": "client_credentials", "clientId": c_id, "clientSecret": c_sec},
                            timeout=20
                        )
                        if auth_res.status_code == 200:
                            return [TextContent(type="text", text="✅ Sucesso! Suas chaves iFood estão ATIVAS e Gerando Tokens.")]
                        return [TextContent(type="text", text=f"❌ Erro nas Chaves iFood: {auth_res.text}")]

                return [TextContent(type="text", text="Comando desconhecido.")]

            _transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ Inteligência MCP Mestre Ativada.")
        except Exception as e:
            logger.error(f"❌ Erro ao subir MCP: {e}")
    return _transport

# --- ENDPOINTS ---
@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "version": "V24-MASTER-BIRDGE", "engine": "Python 3.11"}

@app.get("/mcp")
async def handle_get(request: Request):
    t = await init_mcp_transport()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "BOOT_FAIL"})

@app.post("/mcp")
async def handle_post(request: Request):
    t = await init_mcp_transport()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "BOOT_FAIL"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Motores ligados em 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
