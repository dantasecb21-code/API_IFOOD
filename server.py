import os
import logging
import sys
import httpx
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Carrega variáveis (.env)
load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-bridge")
logger.info("🚩 [V13] MOTOR IFOOD INICIANDO...")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MCP CORE (LAZY LOADED) ---
_transport = None

async def init_mcp():
    global _transport
    if _transport is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            srv = Server("api-ifood-v13")
            
            @srv.list_tools()
            async def list_tools():
                return [
                    Tool(
                        name="get_ifood_kpis",
                        description="Busca KPIs de hoje (pedidos, faturamento, ticket médio) no Supabase.",
                        inputSchema={"type": "object"}
                    ),
                    Tool(
                        name="list_merchants",
                        description="Lista os restaurantes configurados no sistema.",
                        inputSchema={"type": "object"}
                    )
                ]
            
            @srv.call_tool()
            async def call_tool(name, args):
                # Import dinâmico da lógica de banco para não travar o boot
                from supabase import create_client
                url = os.getenv("SUPABASE_URL")
                key = os.getenv("SUPABASE_KEY")
                
                if not url or not key:
                    return [TextContent(type="text", text="❌ Erro: SUPABASE_URL ou KEY não configurados no Railway.")]
                
                supabase = create_client(url, key)
                
                if name == "get_ifood_kpis":
                    # Query real no Supabase Externo (jynlxtamjknauqhviaaq)
                    res = supabase.table("metricas_semanais").select("*").order("created_at", desc=True).limit(1).execute()
                    if res.data:
                        data = res.data[0]
                        msg = f"📊 KPIs de Hoje:\n- Pedidos: {data.get('quantidade_pedidos')}\n- Faturamento: R$ {data.get('vendas_valor')}\n- Ticket Médio: R$ {data.get('ticket_medio')}"
                    else:
                        msg = "⚠️ Nenhuma métrica encontrada para hoje no banco."
                    return [TextContent(type="text", text=msg)]
                
                if name == "list_merchants":
                    res = supabase.table("lojas").select("nome, merchant_id").execute()
                    lojas = ", ".join([f"{l['nome']} ({l['merchant_id']})" for l in res.data]) if res.data else "Nenhuma loja cadastrada."
                    return [TextContent(type="text", text=f"🏠 Restaurantes: {lojas}")]

                return [TextContent(type="text", text="Ferramenta desconhecida.")]

            _transport = FastapiServerTransport(srv, endpoint="/mcp")
            logger.info("✅ MCP V13 Pronto!")
        except Exception as e:
            logger.error(f"❌ Erro Crítico no MCP: {e}")
    return _transport

# --- ROTAS ---
@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "version": "V13-IFOOD-ON"}

@app.get("/mcp")
async def mcp_get(request: Request):
    t = await init_mcp()
    if t: return await t.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "MCP Initialization Failed"})

@app.post("/mcp")
async def mcp_post(request: Request):
    t = await init_mcp()
    if t: return await t.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "MCP Initialization Failed"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
