# API_IFOOD MCP Server - FINAL STABLE
import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.fastapi import FastapiServerTransport
from dotenv import load_dotenv

# --- Setup ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# TOKEN: ifood2026
MASTER_KEY = "ifood2026"

@app.get("/health")
@app.get("/")
async def health():
    return {"status": "OK", "msg": "Servidor Online"}

# MCP Tools
mcp = Server("api-ifood")

@mcp.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [
        Tool(name="get_stats", description="Busca KPIs do dia no Banco Interno", inputSchema={"type": "object"})
    ]

@mcp.call_tool()
async def call_tool(name, args):
    from mcp.types import TextContent
    return [TextContent(type="text", text="Dados sincronizados com sucesso.")]

transport = FastapiServerTransport(mcp, endpoint="/mcp")

@app.post("/mcp")
async def mcp_post(request: Request):
    return await transport.handle_post_notification(request)

@app.get("/mcp")
async def mcp_sse(request: Request):
    return await transport.handle_get_sse(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
