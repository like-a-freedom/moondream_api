class VisionServiceError(Exception):
    """Base exception for vision service errors."""

    pass


class ModelDownloadError(VisionServiceError):
    """Exception raised for errors during model download."""

    pass


class ModelLoadError(VisionServiceError):
    """Exception raised for errors during model loading."""

    pass


class ImageAnalysisError(VisionServiceError):
    """Exception raised for errors during image analysis."""

    pass


class ImageLoadError(VisionServiceError):
    """Exception raised when image loading (URL/base64) fails."""

    pass
