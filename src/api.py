from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from routes import default_router, ollama_router, openai_router
from vision_service import get_vision_service


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the vision service lifecycle."""
    # Startup: initialize the vision service (model download, etc.)
    service = get_vision_service()
    _app.state.vision_service = service
    mode = "api" if service.api_key else "local"
    print(f"Vision service initialized: model={service.model_name}, mode={mode}")
    yield
    # Shutdown: nothing to clean up yet


app = FastAPI(
    title="Moondream API Service",
    description="OpenAI/Ollama-compatible Moondream API Service",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(openai_router, prefix="/v1")
app.include_router(ollama_router, prefix="")
app.include_router(default_router, prefix="")
