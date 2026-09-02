"""
Synthesize a manipulated/deepfake video clip by stitching known ai_modified
test split frames from manifest_combined.csv, and test /api/detect/video endpoint.
"""

import os
import sys
import io
import time
import json
import zipfile
import pandas as pd
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


def load_dataset_zips():
    possible_dirs = [
        r"G:\My Drive\deepfake_project\datasets",
        os.path.abspath("datasets"),
        os.path.join(root_dir, "datasets"),
        r"C:\content\datasets"
    ]
    zips = {}
    for d in possible_dirs:
        p3_path = os.path.join(d, "processed_3class.zip")
        id_path = os.path.join(d, "image_detection.zip")
        if os.path.exists(p3_path) and "processed_3class" not in zips:
            zf = zipfile.ZipFile(p3_path, "r")
            zips["processed_3class"] = {"zip": zf, "namelist_set": set(zf.namelist())}
            print(f"[*] Opened processed_3class zip: {p3_path}")
        if os.path.exists(id_path) and "image_detection" not in zips:
            zf = zipfile.ZipFile(id_path, "r")
            zips["image_detection"] = {"zip": zf, "namelist_set": set(zf.namelist())}
            print(f"[*] Opened image_detection zip: {id_path}")
    return zips


def resolve_image_bytes(image_path: str, zips: dict) -> bytes:
    candidates = [
        image_path,
        os.path.join(root_dir, image_path),
        os.path.join(root_dir, "datasets", image_path)
    ]
    for cand in candidates:
        if os.path.exists(cand) and os.path.isfile(cand):
            with open(cand, "rb") as f:
                return f.read()

    clean_p3 = image_path.replace("processed_3class/", "")
    clean_id = image_path.replace("image_detection/", "")

    if "processed_3class" in zips:
        entry = zips["processed_3class"]
        zf, name_set = entry["zip"], entry["namelist_set"]
        for cand in [image_path, clean_p3]:
            if cand in name_set:
                return zf.read(cand)

    if "image_detection" in zips:
        entry = zips["image_detection"]
        zf, name_set = entry["zip"], entry["namelist_set"]
        for cand in [image_path, clean_id]:
            if cand in name_set:
                return zf.read(cand)

    raise FileNotFoundError(f"Could not locate image file for '{image_path}'")


def create_stitched_deepfake_video(output_video_path: str, num_frames: int = 24, fps: int = 8):
    """Load known ai_modified test frames and stitch them into a real MP4 clip."""
    manifest_path = os.path.join(root_dir, "datasets", "manifest_combined.csv")
    df = pd.read_csv(manifest_path)
    mod_df = df[(df["split"] == "test") & (df["class"] == "ai_modified")].sample(n=num_frames, random_state=123)

    zips = load_dataset_zips()

    frame_arrays = []
    for idx, row in mod_df.iterrows():
        img_bytes = resolve_image_bytes(row["image_path"], zips)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is not None:
            resized = cv2.resize(img_bgr, (256, 256), interpolation=cv2.INTER_LINEAR)
            frame_arrays.append(resized)

    if not frame_arrays:
        raise RuntimeError("No frames could be loaded for video stitching!")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (256, 256))
    for f in frame_arrays:
        out.write(f)
    out.release()

    print(f"[+] Successfully synthesized manipulated video: {output_video_path} ({len(frame_arrays)} frames, {fps} fps, {len(frame_arrays)/fps:.1f}s duration)")
    return len(frame_arrays)


def main():
    print("=" * 85)
    print(" 🎬 SYNTHESIZING & TESTING MANIPULATED/DEEPFAKE VIDEO VIA /api/detect/video")
    print("=" * 85)

    os.makedirs("test_media", exist_ok=True)
    video_path = "test_media/test_manipulated_clip.mp4"

    create_stitched_deepfake_video(video_path, num_frames=24, fps=8)

    app = create_app("development")
    app.config["TESTING"] = True
    client = app.test_client()

    print("\n[*] Sending manipulated video to /api/detect/video...")
    start_time = time.time()
    with open(video_path, "rb") as f:
        res = client.post(
            "/api/detect/video",
            data={"file": (f, "test_manipulated_clip.mp4")},
            content_type="multipart/form-data"
        )
    total_time = time.time() - start_time

    print(f"[*] HTTP Status Code    : {res.status_code}")
    print(f"[*] Total HTTP Latency  : {total_time:.2f}s")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"

    data = json.loads(res.data)

    print("\n" + "=" * 85)
    print(" 📊 DETAILED INFERENCE REPORT FOR MANIPULATED VIDEO")
    print("=" * 85)
    print(f"[*] Model Version        : {data.get('model_version')}")
    print(f"[*] Final Verdict        : {data.get('verdict')}  (Expected: AI-MODIFIED)")
    print(f"[*] Sub-Type Subcategory : {data.get('sub_type')}  (Expected: ai_modified)")
    print(f"[*] Overall Confidence   : {data.get('confidence')}%")
    print(f"[*] Flagged Frames Ratio : {data.get('flagged_ratio_pct')}% ({data.get('flagged_frames_count')} / {data.get('total_sampled_frames')} frames)")
    print(f"[*] Execution Time       : {data.get('execution_time_ms')} ms")
    print(f"[*] Video Metadata       : {data.get('video_metadata')}")
    print(f"[*] Explanation          : {data.get('explanation')}")

    print("\n--- Aggregated Probabilities ---")
    for k, v in data.get("probabilities", {}).items():
        if isinstance(v, float):
            print(f" * {k:<15}: {v*100:6.2f}%")

    print("\n--- Per-Frame Timeline Breakdown (Timeline Chart Data) ---")
    header = f"{'Frame #':<8} | {'Timestamp':<10} | {'Anomaly Score':<14} | {'Flagged?':<10} | {'Frame Pred':<14} | {'p(mod)':<9} | {'p(real)':<9}"
    print(header)
    print("-" * len(header))
    for t in data.get("timeline_analysis", []):
        f_idx = t.get("frame_index")
        ts = t.get("timestamp")
        score = t.get("anomaly_score")
        flag = "FLAGGED [!]" if t.get("is_flagged") else "Normal"
        pred = t.get("sub_type")
        probs = t.get("probabilities", {})
        p_mod = probs.get("ai_modified", 0.0) * 100
        p_real = probs.get("real", 0.0) * 100
        print(f"Frame #{f_idx:<2} | {ts:<10} | {score:6.1f}%       | {flag:<10} | {pred:<14} | {p_mod:6.2f}% | {p_real:6.2f}%")

    print("=" * 85)

    # Cleanup
    if os.path.exists(video_path):
        os.remove(video_path)
    if os.path.exists("test_media"):
        os.rmdir("test_media")


if __name__ == "__main__":
    main()
