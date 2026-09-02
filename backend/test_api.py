"""
Automated unit & integration test suite for the Authenticity Detection API endpoints.
"""

import io
import json
from PIL import Image
try:
    import pytest
except ImportError:
    pytest = None
from app import create_app


def get_test_client():
    app = create_app("development")
    app.config["TESTING"] = True
    return app.test_client()


def _create_test_image_bytes(color=(128, 128, 128), size=(256, 256), fmt="JPEG"):
    """Helper to generate a real, valid image in-memory for testing."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "image_detector" in data["modules"]
    assert "video_detector" in data["modules"]
    assert "document_detector" in data["modules"]
    assert data["modules"]["image_detector"]["mode"] == "production"


def test_modules_info(client):
    response = client.get("/api/modules")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["modules"]) == 3


def test_detect_image_endpoint(client):
    img_buf = _create_test_image_bytes(color=(200, 100, 50))
    test_img = (img_buf, "sample_test.jpg")
    response = client.post(
        "/api/detect/image",
        data={"file": test_img},
        content_type="multipart/form-data"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "verdict" in data
    assert data["verdict"] in ["REAL", "AI-MODIFIED"]
    assert "sub_type" in data
    assert data["sub_type"] in ["ai_generated", "ai_modified", "real"]
    assert "confidence" in data
    assert isinstance(data["confidence"], (int, float))
    assert "probabilities" in data
    assert "ai_generated" in data["probabilities"]
    assert "ai_modified" in data["probabilities"]
    assert "real" in data["probabilities"]
    assert "breakdown" in data
    assert data["module"] == "image_detector"
    assert data["model_version"] == "EfficientNetB0-Authenticity-3Class"


def _create_test_video_path(tmp_path: str = "temp_test_vid.mp4", num_frames: int = 8, fps: int = 10):
    """Generate a real valid mp4 video file with OpenCV for testing."""
    import cv2
    import numpy as np
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp_path, fourcc, fps, (128, 128))
    for i in range(num_frames):
        frame = np.full((128, 128, 3), 100 + i * 15, dtype=np.uint8)
        out.write(frame)
    out.release()
    return tmp_path


def test_detect_video_endpoint(client):
    import os
    vid_path = _create_test_video_path()
    try:
        with open(vid_path, "rb") as f:
            response = client.post(
                "/api/detect/video",
                data={"file": (f, "test_deepfake.mp4")},
                content_type="multipart/form-data"
            )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "verdict" in data
        assert data["verdict"] in ["REAL", "AI-MODIFIED"]
        assert "timeline_analysis" in data
        assert "frame_scores" in data
        assert "probabilities" in data
        assert data["module"] == "video_detector"
        assert len(data["timeline_analysis"]) == 8
    finally:
        if os.path.exists(vid_path):
            os.remove(vid_path)


def test_detect_video_corrupt_file(client):
    fake_vid = (io.BytesIO(b"NOT_A_VALID_MP4_HEADER"), "corrupt.mp4")
    response = client.post(
        "/api/detect/video",
        data={"file": fake_vid},
        content_type="multipart/form-data"
    )
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data


def test_detect_document_mock(client):
    fake_doc = (io.BytesIO(b"%PDF-1.4 FAKE_PDF_CONTENT"), "invoice_scan.pdf")
    response = client.post(
        "/api/detect/document",
        data={"file": fake_doc},
        content_type="multipart/form-data"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "verdict" in data
    assert "tampered_regions" in data
    assert data["module"] == "document_detector"


def test_detect_auto_routing(client):
    import os
    vid_path = _create_test_video_path("temp_auto_test.mp4")
    try:
        with open(vid_path, "rb") as f:
            response = client.post(
                "/api/detect/auto",
                data={"file": (f, "auto_test.mp4")},
                content_type="multipart/form-data"
            )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["module"] == "video_detector"
        assert "verdict" in data
    finally:
        if os.path.exists(vid_path):
            os.remove(vid_path)


def test_invalid_file_extension(client):
    fake_exe = (io.BytesIO(b"MZ executable"), "malicious.exe")
    response = client.post(
        "/api/detect/image",
        data={"file": fake_exe},
        content_type="multipart/form-data"
    )
    assert response.status_code == 400


if __name__ == "__main__":
    print("Running end-to-end backend API test suite...")
    app = create_app("development")
    app.config["TESTING"] = True
    with app.test_client() as c:
        test_health_check(c)
        test_modules_info(c)
        test_detect_image_endpoint(c)
        test_detect_video_endpoint(c)
        test_detect_video_corrupt_file(c)
        test_detect_document_mock(c)
        test_detect_auto_routing(c)
        test_invalid_file_extension(c)
    print("[PASS] All backend API tests including image detector passed successfully!")
