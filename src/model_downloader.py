import gzip
import os
import shutil

import requests

from exceptions import ModelDownloadError


def download_model(model_name: str, dest_path: str) -> str:
    """
    Download and decompress a model file from its configured URL.

    Args:
        model_name: Name of the model (e.g. "moondream-2b-int8").
        dest_path: Path where the decompressed model will be saved.

    Returns:
        The path to the downloaded model file.

    Raises:
        ModelDownloadError: If the model name is unknown, URL is missing,
            or the download/extraction fails.
    """
    url = _resolve_model_url(model_name)
    if not url:
        raise ModelDownloadError(f"Model URL not found for {model_name}")

    try:
        print(f"Downloading model from {url}")
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        wrote = 0
        gz_path = dest_path + ".gz"

        with open(gz_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    _ = f.write(chunk)
                    wrote = wrote + len(chunk)
                    progress = int((wrote / total_size) * 100) if total_size else 0
                    msg = (
                        f"Downloading model: {progress}% "
                        f"({wrote / (1024 * 1024):.2f} MB / "
                        f"{total_size / (1024 * 1024):.2f} MB)"
                    )
                    print(msg, end="\r")

        print()

        with (
            gzip.open(gz_path, "rb") as f_in,
            open(dest_path, "wb") as f_out,
        ):
            shutil.copyfileobj(f_in, f_out)

        os.remove(gz_path)
        return dest_path
    except Exception as e:
        raise ModelDownloadError(f"Error downloading model: {e}")


def _resolve_model_url(model_name: str) -> str | None:
    """Resolve the download URL for a known model name."""
    if model_name == "moondream-2b-int8":
        return os.environ.get("MOONDREAM_2B_URL")
    elif model_name == "moondream-0_5b-int8":
        return os.environ.get("MOONDREAM_500M_URL")
    else:
        return None
