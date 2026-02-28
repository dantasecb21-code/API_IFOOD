import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("mcp-server")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PUBLIC ROUTES ---
@app.get("/health")
@app.get("/")
async def health():
    logger.info("💓 Health check received")
    return {"status": "OK", "version": "RESET-V1"}

@app.get("/mcp")
async def mcp_get():
    # Lovable expects a basic response for discovery
    return {
        "status": "ready",
        "endpoints": ["/mcp"]
    }

@app.post("/mcp")
async def mcp_post(request: Request):
    # Minimal response to prove connectivity
    return JSONResponse({
        "content": [{"type": "text", "text": "Ponte MCP API_IFOOD estabelecida."}]
    })

if __name__ == "__main__":
    import uvicorn
    # Railway dynamic port
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
