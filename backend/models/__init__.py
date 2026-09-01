"""Model inference modules for Image, Video, and Document authenticity detection."""

from .image_detector.model import DeepfakeImageDetector
from .video_detector.model import VideoDeepfakeDetector
from .document_detector.model import DocumentForgeryDetector

__all__ = [
    "DeepfakeImageDetector",
    "VideoDeepfakeDetector",
    "DocumentForgeryDetector",
]
