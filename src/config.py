import os


class Settings:
    MODEL_NAME: str = os.getenv(
        "MODEL_NAME", "moondream3.1-9B-A2B"
    )  # also moondream3-preview available
    MOONDREAM_MODE: str = os.getenv(
        "MOONDREAM_MODE", "api"
    )  # 'api' or 'local' (Photon)
    MOONDREAM_API_KEY: str = os.getenv("MOONDREAM_API_KEY", "")
    MAX_IMAGE_SIZE: int = 2048  # Longest edge, local (Photon) mode


settings = Settings()


def resolve_proxy(target_url: str) -> str | None:
    """Resolve proxy URL for a target URL from standard environment variables.

    Respects the standard proxy convention:
    - ALL_PROXY / all_proxy — fallback for all protocols
    - HTTPS_PROXY / https_proxy — for HTTPS targets
    - HTTP_PROXY / http_proxy — for HTTP targets
    """

    def _env(name: str) -> str | None:
        return os.environ.get(name)

    if target_url.startswith("https://"):
        return (
            _env("HTTPS_PROXY")
            or _env("https_proxy")
            or _env("ALL_PROXY")
            or _env("all_proxy")
        )
    return (
        _env("HTTP_PROXY")
        or _env("http_proxy")
        or _env("ALL_PROXY")
        or _env("all_proxy")
    )
