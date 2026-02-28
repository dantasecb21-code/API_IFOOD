# API_IFOOD MASTER BRIDGE - V25 DEFINITIVE
import os
import logging
import sys
import httpx
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("mcp-v25")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CONFIGURAÇÃO MASTER ---
CLIENT_ID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
CLIENT_SECRET = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"
MERCHANT_UUID = "52d96593-c9fd-4723-8773-760ead971b1b"
MERCHANT_ID = "3634661"

# --- BANCO ---
sb_url = os.getenv("SUPABASE_URL", "https://jynlxtamjknauqhviaaq.supabase.co")
sb_key = os.getenv("SUPABASE_KEY")
supabase = create_client(sb_url, sb_key) if sb_key else None

async def run_ifood_sync():
    """Tenta autenticar no iFood e buscar dados"""
    logger.info("🔄 Iniciando Sincronização V25...")
    try:
        async with httpx.AsyncClient() as client:
            # 1. Login
            auth_res = await client.post(
                "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
                data={"grantType": "client_credentials", "clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET},
                timeout=20
            )
            if auth_res.status_code != 200:
                return f"❌ Erro iFood: {auth_res.text}"
            
            token = auth_res.json().get("accessToken")
            # Aqui poderíamos buscar KPIs e salvar no banco...
            return "✅ Conexão com iFood estabelecida com sucesso!"
    except Exception as e:
        return f"❌ Erro Interno: {str(e)}"

# --- MCP CORE ---
_transport = None

async def get_t():
    global _transport
    if _transport is None:
        from mcp.server import Server
        from mcp.server.fastapi import FastapiServerTransport
        from mcp.types import Tool, TextContent
        
        srv = Server("api-ifood-v25")
        
        @srv.list_tools()
        async def list_tools():
            return [
                Tool(name="sincronizar_agora", description="Força a busca de dados no iFood", inputSchema={"type": "object"}),
                Tool(name="ver_metricas", description="Busca KPIs no Supabase", inputSchema={"type": "object"})
            ]
        
        @srv.call_tool()
        async def call_tool(name, args):
            if name == "sincronizar_agora":
                msg = await run_ifood_sync()
                return [TextContent(type="text", text=msg)]
            return [TextContent(type="text", text="Pronto para processar.")]

        _transport = FastapiServerTransport(srv, endpoint="/mcp")
    return _transport

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "version": "V25-KEYS-FIXED", "merchant": MERCHANT_ID}

@app.get("/mcp")
async def m_get(request: Request):
    t = await get_t()
    return await t.handle_get_sse(request)

@app.post("/mcp")
async def m_post(request: Request):
    t = await get_t()
    return await t.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
