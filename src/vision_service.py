import gzip
import os
import psutil
import shutil
import time
import tiktoken
from typing import Dict, Tuple

import moondream as md
import requests
from PIL import Image

from config import settings
from exceptions import ImageAnalysisError, ModelDownloadError, ModelLoadError


class MoondreamVisionService:
    def __init__(self, base_dir=settings.BASE_MODEL_DIR):
        self.base_dir = os.path.abspath(base_dir)
        self.model_name = settings.MODEL_NAME

        os.makedirs(self.base_dir, exist_ok=True)

        try:
            self.model = self._load_model()
            print(f"Model loaded successfully from {self.base_dir}")
        except Exception as e:
            raise ModelLoadError(f"Failed to initialize vision service: {e}")

    def _load_model(self) -> md.VLM:
        """
        Load the model from local path
        """
        model_path = os.path.join(self.base_dir, self.model_name)
        if not os.path.exists(model_path):
            model_path = self._download_model(model_path)
        return md.vl(model=model_path)

    def _download_model(self, model_path: str) -> str:
        """
        Download the model from the provided URL
        """
        if self.model_name == "moondream-2b-int8":
            url = os.environ.get("MOONDREAM_2B_URL")
        elif self.model_name == "moondream-0_5b-int8":
            url = os.environ.get("MOONDREAM_500M_URL")
        else:
            raise ModelDownloadError(f"Unsupported model name: {self.model_name}")

        if not url:
            raise ModelDownloadError("Model URL not found in environment variables")

        try:
            print(f"Downloading model from {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            block_size = 8192
            wrote = 0

            with open(model_path + ".gz", "wb") as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        wrote = wrote + len(chunk)
                        progress = int((wrote / total_size) * 100) if total_size else 0
                        print(
                            f"Downloading model: {progress}% ({wrote / (1024 * 1024):.2f} MB / {total_size / (1024 * 1024):.2f} MB)",
                            end="\r",
                        )

            with (
                gzip.open(model_path + ".gz", "rb") as f_in,
                open(model_path, "wb") as f_out,
            ):
                shutil.copyfileobj(f_in, f_out)

            os.remove(model_path + ".gz")
            return model_path
        except Exception as e:
            raise ModelDownloadError(f"Error downloading model: {e}")

    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image maintaining aspect ratio"""
        longest_edge = max(image.size)
        if longest_edge > settings.MAX_IMAGE_SIZE:
            scale = settings.MAX_IMAGE_SIZE / longest_edge
            new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        return image

    def calculate_token_cost(self, prompt: str, model_answer: str) -> Tuple[int, int]:
        """
        Calculate the token cost of a prompt
        Args:
            prompt: The prompt to calculate the token cost for
        Returns:
            The token cost of the prompt
        """
        openai_tokenizer = tiktoken.get_encoding("cl100k_base")
        input_tokens = len(prompt)
        output_tokens = len(openai_tokenizer.encode(model_answer))
        return (input_tokens, output_tokens)

    def analyze_image(self, image: Image.Image, user_prompt: str) -> str:
        """
        Analyze an image using the Moondream model
        Args:
            image: The image to analyze
            user_prompt: The user's prompt
        Returns:
            Generated text description
        """
        image = self._resize_image(image)
        encoded_image = self.model.encode_image(image)

        try:
            start_time = time.time()
            answer = self.model.query(
                encoded_image,
                user_prompt,
            )["answer"]
            end_time = time.time()

            execution_time = end_time - start_time
            print(f"Query execution time: {execution_time:.2f} seconds")
            return str(answer).strip()
        except Exception as e:
            raise ImageAnalysisError(f"Error analyzing image: {e}")

    def get_memory_usage(self) -> Dict[str, float]:
        process = psutil.Process()
        memory = process.memory_info()
        return {
            "resident_memory": memory.rss / 1024 / 1024,  # Resident memory in MB
            "virtual_memory": memory.vms / 1024 / 1024,  # Virtual memory in MB
        }
