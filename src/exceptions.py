class VisionServiceError(Exception):
    """Base exception for vision service errors."""

    pass


class ImageAnalysisError(VisionServiceError):
    """Exception raised for errors during image analysis."""

    pass


class ImageLoadError(VisionServiceError):
    """Exception raised when image loading (URL/base64) fails."""

    pass
