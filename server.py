import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

# Logging para vermos o Lovable chegando
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-bridge")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Criamos o Servidor MCP
mcp_server = Server("api-ifood-bridge")

# 2. Adicionamos uma ferramenta de teste
@mcp_server.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [
        Tool(
            name="verificar_ponte",
            description="Verifica se o servidor iFood no Railway está respondendo ao Lovable.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    return [TextContent(type="text", text="🚀 Ponte Ativa! O Lovable está conversando com o seu servidor no Railway.")]

# 3. Configuramos o transporte SSE (que o Lovable exige)
transport = FastapiServerTransport(mcp_server, endpoint="/mcp")

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "info": "Ponte MCP Ativa"}

@app.get("/mcp")
async def mcp_get(request: Request):
    return await transport.handle_get_sse(request)

@app.post("/mcp")
async def mcp_post(request: Request):
    return await transport.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Ponte MCP ligando na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
