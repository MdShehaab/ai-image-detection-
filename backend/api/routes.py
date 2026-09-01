"""
API Blueprint routes for AI-Powered Content Authenticity Detection System.
Provides REST endpoints for Image, Video, and Document deepfake/forgery detection.
"""

import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

from utils.file_utils import (
    is_allowed_file,
    save_uploaded_file,
    cleanup_file,
    infer_module_type,
    get_file_extension
)
from models.image_detector.model import DeepfakeImageDetector
from models.video_detector.model import VideoDeepfakeDetector
from models.document_detector.model import DocumentForgeryDetector

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Singleton model instances initialized on module load
image_detector = DeepfakeImageDetector()
video_detector = VideoDeepfakeDetector()
document_detector = DocumentForgeryDetector()

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend service and model readiness."""
    return jsonify({
        "status": "healthy",
        "service": "AI Content Authenticity Detection API",
        "version": "1.0.0",
        "modules": {
            "image_detector": {
                "name": image_detector.model_name,
                "ready": True,
                "mode": "mock" if not image_detector.is_loaded else "production"
            },
            "video_detector": {
                "name": video_detector.model_name,
                "ready": True,
                "mode": "mock" if not video_detector.is_loaded else "production"
            },
            "document_detector": {
                "name": document_detector.model_name,
                "ready": True,
                "mode": "mock" if not document_detector.is_loaded else "production"
            }
        }
    }), 200

@api_bp.route("/modules", methods=["GET"])
def get_module_info():
    """Retrieve capabilities and supported formats for each detection module."""
    config = current_app.config
    return jsonify({
        "modules": [
            {
                "id": "image",
                "title": "Deepfake Image Detection",
                "description": "Analyzes pixel synthesis, GAN artifacts, frequency domain anomalies, and facial landmark inconsistencies.",
                "supported_extensions": list(config.get("ALLOWED_IMAGE_EXTENSIONS", [])),
                "endpoint": "/api/detect/image"
            },
            {
                "id": "video",
                "title": "AI-Generated Video Detection",
                "description": "Evaluates spatio-temporal dynamics, frame-to-frame warping, blink rates, and lip-sync audio correlation.",
                "supported_extensions": list(config.get("ALLOWED_VIDEO_EXTENSIONS", [])),
                "endpoint": "/api/detect/video"
            },
            {
                "id": "document",
                "title": "Document Forgery Detection",
                "description": "Inspects PDF scans, invoices, and certificates for font mismatch, copy-move stamps, and metadata tampering.",
                "supported_extensions": list(config.get("ALLOWED_DOCUMENT_EXTENSIONS", [])),
                "endpoint": "/api/detect/document"
            }
        ]
    }), 200

@api_bp.route("/detect/image", methods=["POST"])
def detect_image():
    """
    Endpoint: Deepfake Image Detection
    Accepts multipart/form-data with 'file'.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request. Please upload an image using 'file' key."}), 400
        
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400
        
    allowed_exts = current_app.config.get("ALLOWED_IMAGE_EXTENSIONS", {"png", "jpg", "jpeg", "webp"})
    if not is_allowed_file(file.filename, allowed_exts):
        return jsonify({
            "error": f"Invalid file format '{get_file_extension(file.filename)}'. Supported formats: {', '.join(allowed_exts)}"
        }), 400
        
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "./uploads")
    saved_path, original_filename = save_uploaded_file(file, upload_dir)
    
    try:
        results = image_detector.predict(saved_path)
        results["file_name"] = original_filename
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"Image detection pipeline failed: {str(e)}"}), 500
    finally:
        cleanup_file(saved_path)

@api_bp.route("/detect/video", methods=["POST"])
def detect_video():
    """
    Endpoint: AI-Generated Video Detection
    Accepts multipart/form-data with 'file'.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request. Please upload a video using 'file' key."}), 400
        
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400
        
    allowed_exts = current_app.config.get("ALLOWED_VIDEO_EXTENSIONS", {"mp4", "avi", "mov", "mkv", "webm"})
    if not is_allowed_file(file.filename, allowed_exts):
        return jsonify({
            "error": f"Invalid video format '{get_file_extension(file.filename)}'. Supported formats: {', '.join(allowed_exts)}"
        }), 400
        
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "./uploads")
    saved_path, original_filename = save_uploaded_file(file, upload_dir)
    
    try:
        results = video_detector.predict(saved_path)
        results["file_name"] = original_filename
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"Video detection pipeline failed: {str(e)}"}), 500
    finally:
        cleanup_file(saved_path)

@api_bp.route("/detect/document", methods=["POST"])
def detect_document():
    """
    Endpoint: Document Forgery Detection
    Accepts multipart/form-data with 'file'.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request. Please upload a document using 'file' key."}), 400
        
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400
        
    allowed_exts = current_app.config.get("ALLOWED_DOCUMENT_EXTENSIONS", {"pdf", "png", "jpg", "jpeg", "tiff"})
    if not is_allowed_file(file.filename, allowed_exts):
        return jsonify({
            "error": f"Invalid document format '{get_file_extension(file.filename)}'. Supported formats: {', '.join(allowed_exts)}"
        }), 400
        
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "./uploads")
    saved_path, original_filename = save_uploaded_file(file, upload_dir)
    
    try:
        results = document_detector.predict(saved_path)
        results["file_name"] = original_filename
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"Document detection pipeline failed: {str(e)}"}), 500
    finally:
        cleanup_file(saved_path)

@api_bp.route("/detect/auto", methods=["POST"])
def detect_auto():
    """
    Smart auto-routing endpoint. Inspects the file type and forwards it
    to Image, Video, or Document detector automatically.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400
        
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400
        
    module_type = infer_module_type(file.filename, file.mimetype)
    
    if module_type == "image":
        return detect_image()
    elif module_type == "video":
        return detect_video()
    elif module_type == "document":
        return detect_document()
    else:
        return jsonify({
            "error": f"Unable to automatically determine module for file '{file.filename}'. Please select a specific module."
        }), 400
