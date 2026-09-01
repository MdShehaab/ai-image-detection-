import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Application configuration for Content Authenticity Detection System."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-veritas-secret-key-2026")
    
    # Upload settings
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 64 * 1024 * 1024))  # 64 MB max upload
    
    # Supported file extensions per module
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm", "flv"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp"}
    
    # Module Model Configurations
    IMAGE_MODEL_PATH = os.environ.get("IMAGE_MODEL_PATH", str(BASE_DIR / "models" / "weights" / "image_model.h5"))
    VIDEO_MODEL_PATH = os.environ.get("VIDEO_MODEL_PATH", str(BASE_DIR / "models" / "weights" / "video_model.h5"))
    DOCUMENT_MODEL_PATH = os.environ.get("DOCUMENT_MODEL_PATH", str(BASE_DIR / "models" / "weights" / "doc_model.h5"))
    
    # Flag to toggle real vs mock inference until weights are provided
    USE_MOCK_MODELS = os.environ.get("USE_MOCK_MODELS", "True").lower() in ("true", "1", "yes")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
