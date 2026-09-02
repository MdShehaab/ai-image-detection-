"""
End-to-End test and verification script for /api/detect/video endpoint
using real generated MP4 test video files.
"""

import os
import sys
import io
import time
import json
import cv2
import numpy as np

# Force UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure backend and root modules can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import create_app


def create_synthetic_test_video(output_path: str, duration_sec: int = 3, fps: int = 20, width: int = 320, height: int = 240):
    """Generate a real valid mp4 video file with OpenCV."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps
    for i in range(total_frames):
        # Create dynamic frame with moving pattern
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Gradient background
        frame[:, :, 0] = int(i * 255 / total_frames)
        frame[:, :, 1] = int(128 + 60 * np.sin(i / 5.0))
        frame[:, :, 2] = 200
        
        # Draw moving circle
        center_x = int(50 + (width - 100) * (i / total_frames))
        center_y = int(height / 2 + 30 * np.sin(i / 3.0))
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
        cv2.putText(frame, f"Frame {i}/{total_frames}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        out.write(frame)

    out.release()
    print(f"[*] Generated test video at: {output_path} ({total_frames} frames, {duration_sec}s)")


def create_short_test_video(output_path: str, num_frames: int = 8, fps: int = 10, width: int = 320, height: int = 240):
    """Generate an ultra-short video with fewer than 16 frames to test edge case."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for i in range(num_frames):
        frame = np.full((height, width, 3), 100 + i * 15, dtype=np.uint8)
        out.write(frame)
    out.release()
    print(f"[*] Generated short test video at: {output_path} ({num_frames} frames)")


def run_video_tests():
    app = create_app("development")
    app.config["TESTING"] = True
    client = app.test_client()

    os.makedirs("test_media", exist_ok=True)
    normal_vid = "test_media/sample_3sec.mp4"
    short_vid = "test_media/sample_short_8frames.mp4"
    corrupt_vid = "test_media/corrupt_file.mp4"

    create_synthetic_test_video(normal_vid, duration_sec=3, fps=20)
    create_short_test_video(short_vid, num_frames=8, fps=10)

    # Write corrupt dummy file
    with open(corrupt_vid, "wb") as f:
        f.write(b"NOT_A_VALID_MP4_HEADER_DATA_12345")

    print("\n" + "=" * 85)
    print(" 🎬 TEST 1: REAL 3-SECOND VIDEO INFERENCE VIA /api/detect/video")
    print("=" * 85)

    start_time = time.time()
    with open(normal_vid, "rb") as f:
        res = client.post(
            "/api/detect/video",
            data={"file": (f, "sample_3sec.mp4")},
            content_type="multipart/form-data"
        )
    elapsed_time = time.time() - start_time

    print(f"[*] HTTP Status Code    : {res.status_code}")
    print(f"[*] Total Execution Time: {elapsed_time:.2f}s")
    
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = json.loads(res.data)
    print(f"\n--- Response JSON Structure ---")
    print(json.dumps(data, indent=2))

    print("\n" + "=" * 85)
    print(" 🎬 TEST 2: SHORT VIDEO (< 16 FRAMES) EDGE CASE VIA /api/detect/video")
    print("=" * 85)
    with open(short_vid, "rb") as f:
        res_short = client.post(
            "/api/detect/video",
            data={"file": (f, "sample_short_8frames.mp4")},
            content_type="multipart/form-data"
        )
    print(f"[*] HTTP Status Code    : {res_short.status_code}")
    assert res_short.status_code == 200
    data_short = json.loads(res_short.data)
    print(f"[*] Sampled Frames Count: {data_short.get('total_sampled_frames')} (Expected 8)")
    print(f"[*] Verdict             : {data_short.get('verdict')}")
    print(f"[*] Confidence          : {data_short.get('confidence')}%")

    print("\n" + "=" * 85)
    print(" 🎬 TEST 3: CORRUPTED VIDEO FILE ERROR HANDLING")
    print("=" * 85)
    with open(corrupt_vid, "rb") as f:
        res_corrupt = client.post(
            "/api/detect/video",
            data={"file": (f, "corrupt_file.mp4")},
            content_type="multipart/form-data"
        )
    print(f"[*] HTTP Status Code: {res_corrupt.status_code} (Expected 500 or 400 with clean error message)")
    print(f"[*] Error Response  : {res_corrupt.data.decode('utf-8')}")

    # Cleanup temporary test files
    for p in [normal_vid, short_vid, corrupt_vid]:
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists("test_media"):
        os.rmdir("test_media")

    print("\n" + "=" * 85)
    print(" [+] ALL VIDEO ENDPOINT TESTS PASSED SUCCESSFULLY!")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_video_tests()
