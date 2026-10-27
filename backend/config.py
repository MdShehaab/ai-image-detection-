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

    # ── Reference-Check Registry ────────────────────────────────────────────
    # Folder where registered originals are stored (persistent across restarts)
    REGISTRY_FOLDER = os.environ.get("REGISTRY_FOLDER", str(BASE_DIR / "registry" / "data"))

    # Candidate matching thresholds (ORB+phash path)
    REGISTRY_ORB_INLIER_THRESHOLD = int(os.environ.get("REGISTRY_ORB_INLIER_THRESHOLD", 15))
    REGISTRY_PHASH_THRESHOLD      = int(os.environ.get("REGISTRY_PHASH_THRESHOLD",       20))

    # Pixel diff amplitude below this is treated as JPEG/resize noise (0-255)
    REGISTRY_DIFF_AMPLITUDE_CUTOFF = int(os.environ.get("REGISTRY_DIFF_AMPLITUDE_CUTOFF", 25))

    # MODIFIED verdict thresholds (ORB path)
    REGISTRY_MODIFIED_AREA_THRESHOLD   = float(os.environ.get("REGISTRY_MODIFIED_AREA_THRESHOLD",   0.4))
    REGISTRY_MODIFIED_REGION_THRESHOLD = float(os.environ.get("REGISTRY_MODIFIED_REGION_THRESHOLD", 0.15))

    # ── Face Matcher thresholds ──────────────────────────────────────────────
    # Minimum cosine similarity to treat as a face candidate
    # ArcFace ONNX: 0.60 is a good threshold
    # Pixel descriptor (offline fallback): needs a higher bar (~0.88)
    REGISTRY_FACE_SIM_ARCFACE = float(os.environ.get("REGISTRY_FACE_SIM_ARCFACE", 0.60))
    REGISTRY_FACE_SIM_PIXEL   = float(os.environ.get("REGISTRY_FACE_SIM_PIXEL",   0.88))

    # Max allowed shift of face-box centre (fraction of image W/H)
    REGISTRY_FACE_BOX_CENTER_SHIFT = float(os.environ.get("REGISTRY_FACE_BOX_CENTER_SHIFT", 0.12))

    # Allowed face-box size ratio (upload / registered)  [min, max]
    REGISTRY_FACE_SIZE_RATIO_MIN = float(os.environ.get("REGISTRY_FACE_SIZE_RATIO_MIN", 0.75))
    REGISTRY_FACE_SIZE_RATIO_MAX = float(os.environ.get("REGISTRY_FACE_SIZE_RATIO_MAX", 1.33))

    # Max landmark RMSE (normalised [0,1] coords)
    REGISTRY_FACE_LANDMARK_RMSE = float(os.environ.get("REGISTRY_FACE_LANDMARK_RMSE", 0.06))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
