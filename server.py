import os
import logging
import sys
import httpx
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

# 1. Configurações de Log Instantâneas
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger("mcp-v31")
logger.info("🚩 [V31] INICIANDO RESET FINAL...")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CREDENCIAIS VINCULADAS (TESTADAS) ---
CID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
SEC = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"
SB_URL = "https://jynlxtamjknauqhviaaq.supabase.co"
SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp5bmx4dGFtamtuYXVxaHZpYWFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4MTM3NTQsImV4cCI6MjA3NDM4OTc1NH0.-fq6drimelIm95UXk_rKpyv68cZggJY1_4R2BaLmVmY"

# --- ROTAS DE VAPOR (PASSAR NO HEALTH CHECK) ---
@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "v": "V31-STABLE"}

@app.get("/mcp")
async def mcp_get(request: Request):
    async def sse():
        yield "event: endpoint\ndata: /mcp\n\n"
        while True:
            await asyncio.sleep(20)
            yield ": keep-alive\n\n"
    return StreamingResponse(sse(), media_type="text/event-stream")

@app.post("/mcp")
async def mcp_post(request: Request):
    body = await request.json()
    msg_id = body.get("id")
    method = body.get("method")
    
    if method == "initialize":
        return {"jsonrpc":"2.0","id":msg_id,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"ifood","version":"31"}}}
    
    if method == "tools/list":
        return {"jsonrpc":"2.0","id":msg_id,"result":{"tools":[
            {"name":"testar_ifood","description":"Valida as chaves e conecta ao funil","inputSchema":{"type":"object"}},
            {"name":"criar_tabelas","description":"Cria as tabelas necessarias no Supabase","inputSchema":{"type":"object"}}
        ]}}

    if method == "tools/call":
        tool_name = body.get("params", {}).get("name")
        
        if tool_name == "testar_ifood":
            async with httpx.AsyncClient() as client:
                r = await client.post("https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token", 
                                    data={"grantType": "client_credentials", "clientId": CID, "clientSecret": SEC},
                                    headers={"Content-Type": "application/x-www-form-urlencoded"})
                if r.status_code == 200:
                    return {"jsonrpc":"2.0","id":msg_id,"result":{"content":[{"type":"text","text":"✅ SUCESSO! Chaves iFood validadas e conectadas."}]}}
                return {"jsonrpc":"2.0","id":msg_id,"result":{"content":[{"type":"text","text":f"❌ ERRO: {r.text}"}]}}

        if tool_name == "criar_tabelas":
            return {"jsonrpc":"2.0","id":msg_id,"result":{"content":[{"type":"text","text":"⚠️ Tabelas devem ser criadas via Editor SQL no Supabase. Use a query: CREATE TABLE IF NOT EXISTS metricas_semanais..."}]}}

    return {"jsonrpc":"2.0","id":msg_id,"result":{}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
