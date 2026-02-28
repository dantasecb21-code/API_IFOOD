import os
import logging
import sys
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Configuração de Logs direta
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp")

app = FastAPI()

# LIBERA TOTAL PARA O LOVABLE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "msg": "V19 - PRONTO PARA CONECTAR"}

@app.get("/mcp")
async def sse_get(request: Request):
    """O Lovable abre essa porta e espera o sinal de OK"""
    async def event_generator():
        # SINAL ESSENCIAL: Diz ao Lovable onde enviar comandos
        yield f"event: endpoint\ndata: /mcp\n\n"
        while True:
            await asyncio.sleep(20)
            yield ": keep-alive\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/mcp")
async def sse_post(request: Request):
    """O Lovable envia os comandos aqui"""
    body = await request.json()
    msg_id = body.get("id")
    method = body.get("method")
    
    # Resposta de inicialização que o Lovable exige
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ifood-bridge", "version": "1.0.0"}
            }
        }
    
    # Lista a ferramenta de teste
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "verificar_ponte",
                        "description": "Verifica se o servidor iFood está respondendo.",
                        "inputSchema": {"type": "object"}
                    }
                ]
            }
        }
    
    return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

if __name__ == "__main__":
    import uvicorn
    # Railway exige porta dinâmica
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
