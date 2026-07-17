import io
import time

import moondream as md
import psutil
from moondream.types import VLM as VLMClient
from PIL import Image

from config import settings
from exceptions import ImageAnalysisError, ImageLoadError


def load_image(source: str) -> Image.Image:
    """
    Load an image from a URL, data URI, or base64-encoded string.

    Accepts:
    - http/https URLs (fetched via GET)
    - data URIs (``data:image/...;base64,...``)
    - raw base64-encoded image bytes
    """
    try:
        if source.startswith(("http://", "https://")):
            import httpx

            response = httpx.get(source, timeout=30)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        elif source.startswith("data:"):
            import base64

            _, b64_data = source.split(",", 1)
            image_bytes = base64.b64decode(b64_data)
            return Image.open(io.BytesIO(image_bytes))
        else:
            import base64

            image_bytes = base64.b64decode(source)
            return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ImageLoadError(f"Failed to load image: {e}")


class VisionService:
    """Moondream vision service using Cloud API or local Photon inference."""

    def __init__(self, api_key: str = settings.MOONDREAM_API_KEY) -> None:
        self.api_key: str = api_key
        self.model_name: str = settings.MODEL_NAME
        self.local: bool = settings.MOONDREAM_MODE == "local"
        self._client: VLMClient | None = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Moondream client (Cloud or Photon local)."""
        try:
            if self.local:
                self._client = md.vl(
                    api_key=self.api_key,
                    local=True,
                    model=self.model_name,
                )
            else:
                self._client = md.vl(
                    api_key=self.api_key,
                    model=self.model_name,
                )
            mode = "local (Photon)" if self.local else "cloud"
            print(f"Moondream client initialized: mode={mode}, model={self.model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Moondream client: {e}")

    @property
    def model(self) -> VLMClient | None:
        """Access the underlying Moondream client (for health checks, etc.)."""
        return self._client

    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image if it exceeds MAX_IMAGE_SIZE (useful for local mode)."""
        longest_edge = max(image.size)
        if longest_edge > settings.MAX_IMAGE_SIZE:
            scale = settings.MAX_IMAGE_SIZE / longest_edge
            new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        return image

    def analyze_image(self, image: Image.Image, user_prompt: str) -> str:
        """
        Analyze an image using the Moondream model.

        Args:
            image: The image to analyze (PIL Image).
            user_prompt: The user's question about the image.

        Returns:
            Generated text answer.
        """
        image = self._resize_image(image)
        try:
            start_time = time.time()
            client = self._client
            if client is None:
                raise RuntimeError("Moondream client not initialized")
            result = client.query(image, user_prompt)
            end_time = time.time()
            print(f"Query execution time: {end_time - start_time:.2f}s")
            answer = result.get("answer", "")
            return str(answer).strip()
        except Exception as e:
            raise ImageAnalysisError(f"Error analyzing image: {e}")

    def calculate_token_cost(self, prompt: str, model_answer: str) -> tuple[int, int]:
        """
        Estimate token cost for usage reporting.

        In cloud mode the actual token count comes from the Moondream API
        response, but we return a character-based estimate here for the
        OpenAI-compatible usage field.
        """
        return (len(prompt), len(model_answer))

    def get_memory_usage(self) -> dict[str, float]:
        """Get memory usage of the current process in MB."""
        process = psutil.Process()
        memory = process.memory_info()
        return {
            "resident_memory": memory.rss / 1024 / 1024,
            "virtual_memory": memory.vms / 1024 / 1024,
        }


def get_vision_service() -> VisionService:
    return VisionService(api_key=settings.MOONDREAM_API_KEY)
