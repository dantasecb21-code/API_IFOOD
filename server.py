import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- MCP SERVER ---
mcp_srv = Server("api-ifood-v17")

@mcp_srv.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [Tool(name="check", description="Teste", inputSchema={"type": "object"})]

@mcp_srv.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    return [TextContent(type="text", text="✅ Conexão V17 OK!")]

# Transporte SSE
# Criamos uma função para lidar com o transporte de forma segura
transport = FastapiServerTransport(mcp_srv, endpoint="/mcp")

@app.get("/health")
async def health():
    return {"status": "OK", "msg": "V17 - Porta Aberta"}

@app.get("/")
@app.get("/mcp")
async def mcp_get(request: Request):
    return await transport.handle_get_sse(request)

@app.post("/")
@app.post("/mcp")
async def mcp_post(request: Request):
    return await transport.handle_post_notification(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
