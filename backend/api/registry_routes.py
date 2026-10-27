"""
api/registry_routes.py
======================
Blueprint for the Reference-Check registry endpoints.

Routes
------
POST   /api/registry/register   – upload a photo and register it as an original
GET    /api/registry             – list all registered originals
DELETE /api/registry/<id>        – delete one registered original
"""

import os
from flask import Blueprint, request, jsonify, current_app

from utils.file_utils import is_allowed_file, save_uploaded_file, cleanup_file, get_file_extension
import registry.store as store

registry_bp = Blueprint("registry", __name__, url_prefix="/api/registry")


def _get_registry_folder() -> str:
    return current_app.config.get("REGISTRY_FOLDER", "./registry/data")


@registry_bp.route("/register", methods=["POST"])
def register_original():
    """
    POST /api/registry/register

    Accepts multipart/form-data with key 'file'.
    Stores a 512 px thumbnail + perceptual hash; returns the new entry metadata.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Use key 'file'."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty file."}), 400

    allowed_exts = current_app.config.get("ALLOWED_IMAGE_EXTENSIONS", {"png", "jpg", "jpeg", "webp"})
    if not is_allowed_file(file.filename, allowed_exts):
        return jsonify({
            "error": f"Unsupported format '{get_file_extension(file.filename)}'. "
                     f"Supported: {', '.join(sorted(allowed_exts))}"
        }), 400

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "./uploads")
    saved_path, original_filename = save_uploaded_file(file, upload_dir)

    try:
        meta = store.register_original(
            image_path=saved_path,
            original_filename=original_filename,
            registry_base=_get_registry_folder(),
        )
        return jsonify({"success": True, "entry": meta}), 201
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500
    finally:
        cleanup_file(saved_path)


@registry_bp.route("", methods=["GET"])
def list_registry():
    """
    GET /api/registry

    Returns a list of all registered originals sorted newest-first.
    """
    try:
        entries = store.list_originals(_get_registry_folder())
        # Strip internal thumb_path from the public response
        public = []
        for e in entries:
            public.append({
                "id":            e["id"],
                "filename":      e.get("filename", "unknown"),
                "phash":         e.get("phash"),
                "registered_at": e.get("registered_at"),
            })
        return jsonify({"entries": public, "count": len(public)}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to list registry: {str(e)}"}), 500


@registry_bp.route("/<entry_id>", methods=["DELETE"])
def delete_registry_entry(entry_id: str):
    """
    DELETE /api/registry/<id>

    Permanently removes a registered original.
    """
    try:
        success = store.delete_original(entry_id, _get_registry_folder())
        if not success:
            return jsonify({"error": f"Entry '{entry_id}' not found."}), 404
        return jsonify({"success": True, "deleted_id": entry_id}), 200
    except Exception as e:
        return jsonify({"error": f"Deletion failed: {str(e)}"}), 500
