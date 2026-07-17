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
