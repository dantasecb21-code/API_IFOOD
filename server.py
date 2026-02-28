# API_IFOOD MASTER BRIDGE - V27 FINAL RELEASE
import os
import logging
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("mcp-v27")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CREDENCIAIS VINCULADAS ---
CID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
SEC = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"

async def force_ifood_login():
    """Tenta o login com o protocolo RIGOROSO do iFood"""
    logger.info("🔑 Tentando login forçado V27...")
    payload = {
        "grantType": "client_credentials",
        "clientId": CID,
        "clientSecret": SEC
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
                data=payload,
                headers=headers,
                timeout=20
            )
            if res.status_code == 200:
                return "✅ SUCESSO! Conexão iFood estabelecida. Dashboard liberado."
            return f"❌ iFood recusou: {res.text} (Status {res.status_code})"
        except Exception as e:
            return f"❌ Erro de Rede: {str(e)}"

# --- MCP BRIDGE ---
srv = Server("api-ifood-final")
@srv.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [Tool(name="ligar_dashboard", description="Ativa a sincronização iFood", inputSchema={"type":"object"})]

@srv.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    if name == "ligar_dashboard":
        msg = await force_ifood_login()
        return [TextContent(type="text", text=msg)]
    return [TextContent(type="text", text="Pronto.")]

trans = FastapiServerTransport(srv, endpoint="/mcp")

@app.get("/health")
@app.get("/")
async def h():
    return {"status": "OK", "v": "V27-FINAL-RELEASE"}

@app.get("/mcp")
async def g(request: Request):
    return await trans.handle_get_sse(request)

@app.post("/mcp")
async def p(request: Request):
    return await trans.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
