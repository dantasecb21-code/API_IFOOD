import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# --- Basic Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("mcp-debug")

logger.info("Starting Minimalist MCP Server for Debugging...")

# Load env vars
load_dotenv()

# --- Check Env Vars (Masked) ---
def check_env(name):
    val = os.getenv(name)
    if val:
        logger.info(f"Env Var {name}: FOUND (Length: {len(val)})")
        return True
    else:
        logger.warning(f"Env Var {name}: NOT FOUND")
        return False

check_env("SUPABASE_URL")
check_env("SUPABASE_KEY")
check_env("MCP_API_KEY")
check_env("PORT")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Minimalist MCP Debug Server is Running"}

@app.get("/health")
async def health():
    return {"status": "OK", "debug": True}

# O resto do código MCP será adicionado de volta assim que este subir.
# Por enquanto, queremos apenas que o Railway fique VERDE.

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Final Port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
