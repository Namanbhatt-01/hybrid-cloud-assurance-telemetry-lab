import asyncio
import logging
import time
from fastapi import FastAPI, Request
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MOCK-AI] %(message)s")
logger = logging.getLogger("mock_ai_endpoints")

# App 1: Ollama API (Port 11434)
ollama_app = FastAPI(title="Mock Ollama Engine", version="1.0.0")

@ollama_app.get("/api/tags")
async def ollama_tags():
    return {
        "models": [
            {"name": "llama3:8b", "size": 4661224676, "digest": "365c0bd3c000"},
            {"name": "mistral:7b", "size": 4109865159, "digest": "61e88e88e606"}
        ]
    }

@ollama_app.post("/api/generate")
async def ollama_generate(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    model = body.get("model", "llama3:8b")
    # Simulate realistic token generation time (50ms)
    await asyncio.sleep(0.05)
    return {
        "model": model,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "response": f"Synthetic response for: {prompt[:30]}",
        "done": True,
        "total_duration": 50000000,
        "eval_count": 24
    }

# App 2: HuggingFace Inference API (Port 8088)
hf_app = FastAPI(title="Mock HuggingFace API", version="1.0.0")

@hf_app.get("/models/meta-llama")
async def hf_model_status():
    return {"id": "meta-llama/Meta-Llama-3-8B-Instruct", "pipeline_tag": "text-generation", "status": "active"}

@hf_app.post("/models/meta-llama/Llama-3-8B")
async def hf_infer(request: Request):
    await asyncio.sleep(0.04)
    return [{"generated_text": "HuggingFace inference API synthetic verification response."}]

async def main():
    config_ollama = uvicorn.Config(ollama_app, host="0.0.0.0", port=11434, log_level="info")
    config_hf = uvicorn.Config(hf_app, host="0.0.0.0", port=8088, log_level="info")

    server_ollama = uvicorn.Server(config_ollama)
    server_hf = uvicorn.Server(config_hf)

    await asyncio.gather(
        server_ollama.serve(),
        server_hf.serve()
    )

if __name__ == "__main__":
    asyncio.run(main())
