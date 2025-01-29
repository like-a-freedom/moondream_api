import base64
import io
import time
from datetime import datetime, timezone

import requests
from fastapi import APIRouter, HTTPException
from PIL import Image

from ollama_model_mocks import MOCK_MOONDREAM_MODEL_DATA
from config import settings
from exceptions import VisionServiceException
from schemas import (
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    OllamaMessage,
    OllamaRequest,
    OllamaResponse,
    OllamaModelShowResponse,
    OllamaShowModelRequest,
)
from vision_service import MoondreamVisionService

openai_router = APIRouter()
ollama_router = APIRouter()
default_router = APIRouter()
vision_service = MoondreamVisionService()


@openai_router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest):
    try:
        last_message = request.messages[-1]
        image_url = None
        prompt = None

        if isinstance(last_message.content, list):
            for content in last_message.content:
                if isinstance(content, dict):
                    if content.get("type") == "image_url":
                        image_url = content["image_url"]["url"]
                    elif content.get("type") == "text":
                        prompt = content["text"]

                # Handle structured content
                if hasattr(content, "type"):
                    if content.type == "image_url":
                        image_url = content.image_url.url
                    elif content.type == "text":
                        prompt = content.text

        if not image_url:
            raise HTTPException(status_code=400, detail="No image URL provided")
        if not prompt:
            raise HTTPException(status_code=400, detail="No text prompt provided")

        # Download and process image
        try:
            response = requests.get(image_url)
            image = Image.open(io.BytesIO(response.content))
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to load image: {str(e)}"
            )

        text_answer = vision_service.analyze_image(image, prompt)
        usage_stats = vision_service.calculate_token_cost(prompt, text_answer)

        return ChatCompletionResponse(
            id=f"chatcmpl-{int(time.time())}",
            created=int(time.time()),
            model=request.model or settings.MODEL_NAME,
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

    except VisionServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ollama_router.post("/api/chat", response_model=OllamaResponse)
async def ollama_chat_completion(request: OllamaRequest):
    try:
        last_message = request.messages[-1]
        image_data = None
        prompt = None

        if isinstance(last_message.content, list):
            # Handle structured content
            for content in last_message.content:
                if isinstance(content, dict):
                    if content.get("type") == "image":
                        # Handle image URL
                        image_url = content.get("image")
                        if image_url and image_url.startswith("http"):
                            response = requests.get(image_url)
                            image_data = base64.b64encode(response.content).decode(
                                "utf-8"
                            )
                    elif content.get("type") == "text":
                        prompt = content.get("text")
        else:
            # Handle simple content
            prompt = last_message.content
            if last_message.images and len(last_message.images) > 0:
                image_data = last_message.images[0]

        if not image_data:
            raise HTTPException(status_code=400, detail="No image provided")
        if not prompt:
            raise HTTPException(status_code=400, detail="No text prompt provided")

        try:
            # Decode base64 image or download URL
            if image_data.startswith("http"):
                response = requests.get(image_data)
                image = Image.open(io.BytesIO(response.content))
            else:
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

        # Process image and generate response
        answer = vision_service.analyze_image(image, prompt)

        return OllamaResponse(
            model=request.model or settings.MODEL_NAME,
            created_at=datetime.now(timezone.utc).isoformat(),
            message=OllamaMessage(role="assistant", content=answer),
            done=True,
        )

    except VisionServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ollama_router.post("/api/show", response_model=OllamaModelShowResponse)
async def ollama_show_model(request: OllamaShowModelRequest):
    if request.model not in ("moondream" or "moondream2"):
        raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
    return MOCK_MOONDREAM_MODEL_DATA


@default_router.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Check if model is loaded
        if not vision_service or not vision_service.model:
            return {
                "status": "error",
                "message": "Vision service not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Get memory stats
        memory_stats = vision_service.get_memory_usage()

        return {
            "status": "healthy",
            "model": vision_service.model_name,
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
