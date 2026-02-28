# API_IFOOD MCP Server - V14 TOTAL AUTOMATION
import os
import logging
import sys
import asyncio
import httpx
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("api-ifood-v14")
logger.info("🚩 [V14] MOTOR AUTOMATIZADO INICIANDO...")

app = FastAPI(title="API_IFOOD Automation Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG & STATE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CLIENT_ID = os.getenv("IFOOD_CLIENT_ID")
CLIENT_SECRET = os.getenv("IFOOD_CLIENT_SECRET")

# Instância do Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# --- IFOOD SYNC LOGIC ---
async def run_ifood_sync():
    """Lógica principal de sincronização iFood -> Supabase"""
    logger.info("🔄 Iniciando sincronização automática iFood...")
    if not all([CLIENT_ID, CLIENT_SECRET, supabase]):
        logger.error("❌ Credenciais ausentes no .env (CLIENT_ID, CLIENT_SECRET ou SUPABASE)")
        return "Erro: Credenciais incompletas."
    
    try:
        # 1. Login no iFood
        async with httpx.AsyncClient() as client:
            auth_res = await client.post(
                "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
                data={
                    "grantType": "client_credentials",
                    "clientId": CLIENT_ID,
                    "clientSecret": CLIENT_SECRET
                },
                timeout=30
            )
            if auth_res.status_code != 200:
                return f"Erro iFood Auth: {auth_res.text}"
            
            token = auth_res.json().get("accessToken")
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Busca lojas cadastradas no SEU banco
            res_lojas = supabase.table("lojas").select("merchant_id, nome").execute()
            status_report = []
            
            for loja in res_lojas.data:
                m_id = loja['merchant_id']
                # 3. Busca vendas do dia
                sales_res = await client.get(
                    f"https://merchant-api.ifood.com.br/financial/v1.0/merchants/{m_id}/sales",
                    headers=headers,
                    params={"beginOrderDate": datetime.now().strftime("%Y-%m-%d"), "endOrderDate": datetime.now().strftime("%Y-%m-%d")},
                    timeout=30
                )
                
                if sales_res.status_code == 200:
                    vendas = sales_res.json()
                    total_valor = sum(o.get('total', {}).get('value', 0) for o in vendas)
                    total_pedidos = len(vendas)
                    
                    # 4. Salva no banco (Tabela: metricas_semanais)
                    supabase.table("metricas_semanais").insert({
                        "merchant_id": m_id,
                        "vendas_valor": total_valor,
                        "quantidade_pedidos": total_pedidos,
                        "fonte_dados": "api_ifood_auto",
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    status_report.append(f"✅ {loja['nome']}: R${total_valor} ({total_pedidos} pedidos)")
                else:
                    status_report.append(f"⚠️ {loja['nome']}: Erro API {sales_res.status_code}")
            
            return "\n".join(status_report)
    except Exception as e:
        logger.error(f"❌ Falha na sincronização: {e}")
        return f"Erro interno: {str(e)}"

# --- BACKGROUND TASK ---
async def scheduler_loop():
    """Roda a sincronização a cada 1 hora enquanto o servidor estiver ativo"""
    while True:
        try:
            await run_ifood_sync()
        except Exception as e:
            logger.error(f"Erro no loop do scheduler: {e}")
        await asyncio.sleep(3600)  # 1 hora

@app.on_event("startup")
async def startup_event():
    # Inicia o loop em background sem travar o boot do servidor
    asyncio.create_task(scheduler_loop())

# --- MCP BRIDGE ---
_transport = None

async def get_mcp_transport():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood-auto-v14")
            
            @srv.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_ifood_kpis", description="Busca os KPIs salvos no Supabase hoje.", inputSchema={"type": "object"}),
                    Tool(name="sync_ifood_now", description="Dispara a sincronização manual com o iFood agora.", inputSchema={"type": "object"}),
                    Tool(name="list_merchants", description="Lista os restaurantes ativos.", inputSchema={"type": "object"})
                ]
            
            @srv.call_tool()
            async def call_tool(name, args):
                if name == "sync_ifood_now":
                    result = await run_ifood_sync()
                    return [TextContent(type="text", text=f"Sincronização Finalizada:\n{result}")]
                
                if name == "get_ifood_kpis":
                    if not supabase: return [TextContent(type="text", text="❌ Erro: Banco não configurado.")]
                    res = supabase.table("metricas_semanais").select("*").order("created_at", desc=True).limit(5).execute()
                    metrics = "\n".join([f"- {m.get('created_at')[:16]}: R${m.get('vendas_valor')} ({m.get('quantidade_pedidos')} pedidos)" for m in res.data])
                    return [TextContent(type="text", text=f"📈 Últimas Métricas:\n{metrics}")]
                
                if name == "list_merchants":
                    if not supabase: return [TextContent(type="text", text="❌ Erro: Banco não configurado.")]
                    res = supabase.table("lojas").select("nome, merchant_id").execute()
                    lojas = "\n".join([f"- {l['nome']} ({l['merchant_id']})" for l in res.data])
                    return [TextContent(type="text", text=f"🏠 Restaurantes:\n{lojas}")]
                
                return [TextContent(type="text", text="Ferramenta não encontrada.")]

            _transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ MCP Intelegence Active.")
        except Exception as e:
            logger.error(f"❌ Falha ao carregar MCP: {e}")
    return _transport

# --- ENDPOINTS ---
@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "msg": "V14 - Automação iFood Ativa", "db": "OK" if supabase else "FAIL"}

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await get_mcp_transport()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP Offline"})

@app.post("/mcp")
async def mcp_post(request: Request):
    t = await get_mcp_transport()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP Offline"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
