from fastapi import FastAPI
from routes import ollama_router, openai_router, default_router

app = FastAPI(
    title="Moondream API Service",
    description="OpenAI/Ollama-compatible Moondream API Service",
    version="1.0.0",
)
app.include_router(openai_router, prefix="/v1")
app.include_router(ollama_router, prefix="")
app.include_router(default_router, prefix="")
