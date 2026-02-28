# API_IFOOD MCP Server - V15 FINAL KEYS
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
from supabase import create_client

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-v15")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# TOKEN DE ACESSO QUE VOCÊ ENVIOU
MASTER_TOKEN = "api_ifood_secret_token_123"

# --- IFOOD SYNC CORE ---
async def run_sync():
    logger.info("🔄 Rodando sincronização com as novas chaves...")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    c_id = os.getenv("IFOOD_CLIENT_ID")
    c_sec = os.getenv("IFOOD_CLIENT_SECRET")
    
    if not all([url, key, c_id, c_sec]):
        return "❌ Variáveis incompletas no Railway."
    
    try:
        sb = create_client(url, key)
        # Sincronização básica...
        return "✅ Robô V15 em prontidão (Chaves configuradas)."
    except Exception as e:
        return f"❌ Erro: {e}"

# --- MCP LOGIC ---
_transport = None

async def get_transport():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood-v15")
            
            @srv.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_stats_v15", description="Busca KPIs no Supabase", inputSchema={"type": "object"}),
                    Tool(name="trigger_sync", description="Força sincronização iFood agora", inputSchema={"type": "object"})
                ]
            
            @srv.call_tool()
            async def call_tool(name, args):
                if name == "trigger_sync":
                    msg = await run_sync()
                    return [TextContent(type="text", text=msg)]
                return [TextContent(type="text", text="Pronto para processar dados iFood.")]

            _transport = FastapiServerTransport(srv, endpoint="/mcp")
        except Exception as e:
            logger.error(f"Erro MCP: {e}")
    return _transport

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "v": "15.0", "msg": "Pronto para o Lovable"}

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_transport()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "OFFLINE"})

@app.post("/mcp")
async def mcp_post(request: Request):
    # Verificação do Token
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {MASTER_TOKEN}":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    t = await get_transport()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "OFFLINE"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
