# API_IFOOD MASTER BRIDGE - V26 DEBUG FORCE
import os
import logging
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("mcp-v26")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CREDENCIAIS FIXAS (UUID) ---
CID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
SEC = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"

async def test_auth():
    """Tenta autenticar de dois jeitos diferentes"""
    logger.info(f"🔑 Testando chaves (Tamanho ID: {len(CID)}, Tamanho SEC: {len(SEC)})")
    async with httpx.AsyncClient() as client:
        # Tentativa 1: CamelCase (Padrão iFood v1.0)
        res = await client.post(
            "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
            data={"grantType": "client_credentials", "clientId": CID, "clientSecret": SEC},
            timeout=15
        )
        if res.status_code == 200:
            return "✅ SUCESSO! Login Centralizado (C) OK."
        
        # Tentativa 2: Snake Case (Backup)
        res2 = await client.post(
            "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
            data={"grant_type": "client_credentials", "client_id": CID, "client_secret": SEC},
            timeout=15
        )
        if res2.status_code == 200:
            return "✅ SUCESSO! Login com Formato Snake_Case OK."
            
        return f"❌ FALHA FINAL: iFood diz '{res.text}' (Status {res.status_code})"

# --- MCP BRIDGE ---
srv = Server("api-ifood-debug")
@srv.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [Tool(name="testar_conexao_real", description="Tenta logar no iFood AGORA", inputSchema={"type":"object"})]

@srv.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    if name == "testar_conexao_real":
        msg = await test_auth()
        return [TextContent(type="text", text=msg)]
    return [TextContent(type="text", text="Pronto.")]

trans = FastapiServerTransport(srv, endpoint="/mcp")

@app.get("/health")
@app.get("/")
async def h():
    return {"status": "OK", "v": "V26-DEBUG-FORCE"}

@app.get("/mcp")
async def g(request: Request):
    return await trans.handle_get_sse(request)

@app.post("/mcp")
async def p(request: Request):
    return await trans.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
