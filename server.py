import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Minimal logging for speed
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MASTER_TOKEN = "api_ifood_secret_token_123"

# --- MCP TRANS ---
_t = None

def get_t():
    global _t
    if _t is None:
        try:
            from mcp.server import Server
            from mcp.server.fastapi import FastapiServerTransport
            from mcp.types import Tool, TextContent
            
            s = Server("api-ifood-v16")
            @s.list_tools()
            async def list_tools():
                return [
                    Tool(name="get_ifood_stats", description="Ver faturamento hoje", inputSchema={"type":"object"}),
                    Tool(name="sync_ifood", description="Sincronizar dados agora", inputSchema={"type":"object"})
                ]
            
            @s.call_tool()
            async def call_tool(name, args):
                return [TextContent(type="text", text="✅ Ponte V16 conectada e operando.")]
                
            _t = FastapiServerTransport(s, endpoint="/mcp")
        except Exception as e:
            logger.error(f"Err: {e}")
    return _t

@app.get("/health")
@app.get("/")
async def h():
    return {"status": "OK", "v": "16.0"}

@app.get("/mcp")
async def m_get(request: Request):
    transport = get_t()
    if transport: return await transport.handle_get_sse(request)
    return JSONResponse(status_code=500, content={"error": "BOOT_ERR"})

@app.post("/mcp")
async def m_post(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {MASTER_TOKEN}":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    transport = get_t()
    if transport: return await transport.handle_post_notification(request)
    return JSONResponse(status_code=500, content={"error": "BOOT_ERR"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
