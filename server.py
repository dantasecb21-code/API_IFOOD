import os
import logging
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-v30")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CREDENCIAIS VINCULADAS ---
CID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
SEC = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "v": "V30-READY"}

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
        return {"jsonrpc":"2.0","id":msg_id,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"ifood","version":"1"}}}
    
    if method == "tools/list":
        return {"jsonrpc":"2.0","id":msg_id,"result":{"tools":[{"name":"sincronizar_ifood","description":"Faz login real no iFood","inputSchema":{"type":"object"}}]}}

    if method == "tools/call":
        async with httpx.AsyncClient() as client:
            # TENTA O PADRÃO 1
            r = await client.post("https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token", 
                                data={"grantType": "client_credentials", "clientId": CID, "clientSecret": SEC},
                                headers={"Content-Type": "application/x-www-form-urlencoded"})
            if r.status_code == 200:
                return {"jsonrpc":"2.0","id":msg_id,"result":{"content":[{"type":"text","text":"✅ SUCESSO! Logado no iFood."}]}}
            
            # TENTA O PADRÃO 2 (Se o 1 falhar)
            r2 = await client.post("https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token", 
                                 data={"grant_type": "client_credentials", "client_id": CID, "client_secret": SEC},
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
            
            return {"jsonrpc":"2.0","id":msg_id,"result":{"content":[{"type":"text","text":f"❌ Erro iFood: {r.text}"}]}}

    return {"jsonrpc":"2.0","id":msg_id,"result":{}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
