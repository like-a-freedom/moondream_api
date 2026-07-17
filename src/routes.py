import json
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from config import settings
from exceptions import VisionServiceError
from ollama_model_mocks import MOCK_MOONDREAM_MODEL_DATA
from schemas import (
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    OllamaChatRequest,
    OllamaChatResponse,
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OllamaMessage,
    OllamaModelShowResponse,
    OllamaShowModelRequest,
)
from vision_service import VisionService, load_image

# ── OpenAI SSE streaming helpers ──────────────────────────────────────────


def _make_streaming_chunk(
    chunk_id: str,
    created: int,
    model: str,
    *,
    delta_content: str | None = None,
    finish_reason: str | None = None,
) -> str:
    """Build an SSE ``data:`` line matching the OpenAI chat completion chunk format."""
    delta: dict[str, str] = {}
    if delta_content is not None:
        delta["content"] = delta_content
    choice = {
        "index": 0,
        "delta": delta,
        "logprobs": None,
        "finish_reason": finish_reason,
    }
    payload = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "system_fingerprint": None,
        "choices": [choice],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _openai_stream_generator(
    vs: VisionService,
    image_url: str,
    prompt: str,
    model: str,
) -> AsyncGenerator[str, None]:
    """Yield SSE ``data:`` lines for an OpenAI streaming response."""
    chunk_id = f"chatcmpl-{int(time.time())}"
    created = int(time.time())

    image = load_image(image_url)
    # Run inference; we don't have per-token streaming from the local model,
    # so we yield the full answer as a single delta.
    answer = vs.analyze_image(image, prompt)

    # Role announcement
    yield _make_streaming_chunk(chunk_id, created, model, delta_content="")

    # Content delta (entire answer)
    yield _make_streaming_chunk(chunk_id, created, model, delta_content=answer)

    # Final chunk with finish_reason
    yield _make_streaming_chunk(chunk_id, created, model, finish_reason="stop")

    yield "data: [DONE]\n\n"


openai_router = APIRouter()
ollama_router = APIRouter()
default_router = APIRouter()


def _extract_openai_content(
    last_message: ChatMessage,
) -> tuple[str | None, str | None]:
    """Extract image URL and text prompt from an OpenAI-style message."""
    image_url = None
    prompt = None

    if isinstance(last_message.content, list):
        for part in last_message.content:
            if isinstance(part, dict):
                if part.get("type") == "image_url":
                    image_url = part["image_url"]["url"]
                elif part.get("type") == "text":
                    prompt = part["text"]
            elif hasattr(part, "type"):
                if part.type == "image_url":
                    image_url = part.image_url.url
                elif part.type == "text":
                    prompt = part.text

    return image_url, prompt


def _extract_ollama_chat_content(
    last_message: OllamaMessage,
) -> tuple[str | None, str | None]:
    """Extract image data and text prompt from an Ollama-style chat message."""
    image_data = None
    prompt = None

    if isinstance(last_message.content, list):
        for part in last_message.content:
            if isinstance(part, dict):
                if part.get("type") == "image":
                    raw = part.get("image")
                    if raw and raw.startswith(("http://", "https://")):
                        # For URL images in Ollama chat, we keep the URL as-is;
                        # load_image will handle the download.
                        image_data = raw
                    elif raw:
                        image_data = raw
                elif part.get("type") == "text":
                    prompt = part.get("text")
    else:
        prompt = last_message.content
        if last_message.images:
            image_data = last_message.images[0]

    return image_data, prompt


def _get_service(request: Request) -> VisionService:
    """Get the vision service instance from the app lifespan state."""
    return request.app.state.vision_service


@openai_router.post("/chat/completions")
async def chat_completion(
    request: Request,
    body: ChatCompletionRequest,
):
    try:
        vs = _get_service(request)
        last_message = body.messages[-1]
        image_url, prompt = _extract_openai_content(last_message)

        if not image_url:
            raise HTTPException(status_code=400, detail="No image URL provided")
        if not prompt:
            raise HTTPException(status_code=400, detail="No text prompt provided")

        # ── Streaming path ──────────────────────────────────────────────
        if body.stream:
            return StreamingResponse(
                _openai_stream_generator(
                    vs, image_url, prompt, body.model or settings.MODEL_NAME
                ),
                media_type="text/event-stream",
            )

        # ── Non-streaming path ──────────────────────────────────────────
        image = load_image(image_url)
        text_answer = vs.analyze_image(image, prompt)
        usage_stats = vs.calculate_token_cost(prompt, text_answer)

        return ChatCompletionResponse(
            id=f"chatcmpl-{int(time.time())}",
            created=int(time.time()),
            model=body.model or settings.MODEL_NAME,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=text_answer),
                    finish_reason="stop",
                )
            ],
            usage={
                "prompt_tokens": usage_stats[0],
                "completion_tokens": usage_stats[1],
                "total_tokens": sum(usage_stats),
            },
        )

    except VisionServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ollama_router.post("/api/chat", response_model=OllamaChatResponse)
async def ollama_chat_completion(request: Request, body: OllamaChatRequest):
    try:
        vs = _get_service(request)
        last_message = body.messages[-1]
        image_data, prompt = _extract_ollama_chat_content(last_message)

        if not image_data:
            raise HTTPException(status_code=400, detail="No image provided")
        if not prompt:
            raise HTTPException(status_code=400, detail="No text prompt provided")

        image = load_image(image_data)
        answer = vs.analyze_image(image, prompt)

        return OllamaChatResponse(
            model=body.model or settings.MODEL_NAME,
            created_at=datetime.now(timezone.utc).isoformat(),
            message=OllamaMessage(role="assistant", content=answer),
            done=True,
        )

    except VisionServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ollama_router.post("/api/generate", response_model=OllamaGenerateResponse)
async def generate(request: Request, body: OllamaGenerateRequest):
    try:
        start_time = time.time_ns()
        load_start = time.time_ns()

        vs = _get_service(request)
        prompt = body.prompt

        if not body.images:
            raise HTTPException(status_code=400, detail="No images provided")

        images = []
        for image_data in body.images:
            images.append(load_image(image_data))

        load_duration = time.time_ns() - load_start

        prompt_eval_start = time.time_ns()
        answers: list[str] = []
        for img in images:
            answers.append(vs.analyze_image(img, prompt))

        prompt_eval_duration = time.time_ns() - prompt_eval_start
        total_duration = time.time_ns() - start_time

        combined_answer = answers[0]

        return OllamaGenerateResponse(
            model=body.model or settings.MODEL_NAME,
            created_at=datetime.now(timezone.utc).isoformat(),
            response=combined_answer,
            done=True,
            context=[],
            total_duration=total_duration,
            load_duration=load_duration,
            prompt_eval_count=len(prompt),
            prompt_eval_duration=prompt_eval_duration,
            eval_count=len(combined_answer),
            eval_duration=total_duration - load_duration - prompt_eval_duration,
        )

    except VisionServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ollama_router.post("/api/show", response_model=OllamaModelShowResponse)
async def ollama_show_model(body: OllamaShowModelRequest):
    if body.model not in ("moondream", "moondream2"):
        raise HTTPException(status_code=404, detail=f"Model {body.model} not found")
    return MOCK_MOONDREAM_MODEL_DATA


@default_router.get("/health")
async def health_check(request: Request):
    """Health check endpoint for container orchestration."""
    try:
        vs = getattr(request.app.state, "vision_service", None)
        if not vs or not vs.model:
            return {
                "status": "initializing",
                "message": "Vision service not yet initialized",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        memory_stats = vs.get_memory_usage()

        return {
            "status": "healthy",
            "model": vs.model_name,
            "memory": {
                "resident_mb": f"{memory_stats['resident_memory']:.2f}",
                "virtual_mb": f"{memory_stats['virtual_memory']:.2f}",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
