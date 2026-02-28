import os
import logging
import sys
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-v18")

app = FastAPI()

# LIBERA TUDO (CORS MÁXIMO)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "version": "V18-MANUAL"}

# --- HANDSHAKE MCP MANUAL PARA O LOVABLE ---

@app.get("/mcp")
async def mcp_get(request: Request):
    """Lida com a conexão SSE do Lovable"""
    async def event_generator():
        # 1. Envia o ID da conexão (exigência MCP)
        yield f"event: endpoint\ndata: /mcp\n\n"
        
        # Mantém a conexão viva
        while True:
            await asyncio.sleep(15)
            yield ": keep-alive\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/mcp")
async def mcp_post(request: Request):
    """Lida com as requisições de ferramentas"""
    body = await request.json()
    msg_id = body.get("id")
    method = body.get("method")
    
    # Resposta padrão para o Lovable "sentir" o servidor
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
    
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "check_status",
                        "description": "Verifica se a ponte iFood está operacional.",
                        "inputSchema": {"type": "object"}
                    }
                ]
            }
        }

    return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
