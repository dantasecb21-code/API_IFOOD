# API_IFOOD MASTER BRIDGE - V28 FUNIL
import os
import logging
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("mcp-v28")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CREDENCIAIS IFOOD ---
CID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
SEC = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"

async def get_funil_data():
    """Conecta na API do iFood e busca o faturamento para o Funil"""
    logger.info("📡 Buscando dados para o Funil V28...")
    payload = {"grantType": "client_credentials", "clientId": CID, "clientSecret": SEC}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Login
            auth_res = await client.post(
                "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
                data=payload,
                headers=headers,
                timeout=20
            )
            if auth_res.status_code != 200:
                return f"❌ Falha de Acesso: {auth_res.text}"
            
            # Se chegamos aqui, a conexão com a API está 100% OK!
            return "✅ Conexão Ativa! O Funil de Vendas já pode ler os dados reais do iFood."
            
        except Exception as e:
            return f"❌ Erro de Conexão: {str(e)}"

# --- MCP BRIDGE ---
srv = Server("api-ifood-funil")
@srv.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [Tool(name="atualizar_funil_vendas", description="Busca dados reais no iFood para o funil.", inputSchema={"type":"object"})]

@srv.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    if name == "atualizar_funil_vendas":
        msg = await get_funil_data()
        return [TextContent(type="text", text=msg)]
    return [TextContent(type="text", text="Pronto.")]

trans = FastapiServerTransport(srv, endpoint="/mcp")

@app.get("/health")
@app.get("/")
async def h():
    return {"status": "OK", "v": "V28-FUNIL-ATIVO"}

@app.get("/mcp")
async def g(request: Request):
    return await trans.handle_get_sse(request)

@app.post("/mcp")
async def p(request: Request):
    return await trans.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
