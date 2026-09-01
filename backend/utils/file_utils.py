import os
import uuid
from werkzeug.utils import secure_filename

def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension without leading dot."""
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""

def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is in allowed set."""
    ext = get_file_extension(filename)
    return ext in allowed_extensions

def infer_module_type(filename: str, mimetype: str = "") -> str:
    """
    Infer target detection module based on file extension and MIME type.
    Returns: 'image', 'video', 'document', or 'unknown'
    """
    ext = get_file_extension(filename)
    
    if ext == "pdf":
        return "document"
    elif ext in {"mp4", "avi", "mov", "mkv", "webm", "flv"}:
        return "video"
    elif ext in {"png", "jpg", "jpeg", "webp", "bmp"}:
        # In a real pipeline, user can also choose document mode for images.
        return "image"
    elif ext == "tiff":
        return "document"
    
    if mimetype:
        if mimetype.startswith("image/"):
            return "image"
        elif mimetype.startswith("video/"):
            return "video"
        elif mimetype == "application/pdf":
            return "document"
            
    return "unknown"

def save_uploaded_file(file_storage, target_dir: str) -> tuple[str, str]:
    """
    Save Werkzeug FileStorage safely with UUID prefix to prevent collisions.
    Returns (saved_path, original_filename).
    """
    os.makedirs(target_dir, exist_ok=True)
    original_name = secure_filename(file_storage.filename or "unnamed_upload")
    unique_prefix = uuid.uuid4().hex[:12]
    saved_filename = f"{unique_prefix}_{original_name}"
    saved_path = os.path.join(target_dir, saved_filename)
    
    file_storage.save(saved_path)
    return saved_path, original_name

def cleanup_file(filepath: str) -> None:
    """Safely remove a temporary file if it exists."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"[WARN] Failed to cleanup file {filepath}: {e}")
