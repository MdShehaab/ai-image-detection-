"""
Script to:
1. Run the real-world user video through /api/detect/video and output the full response JSON.
2. Inspect sample training images from processed_3class train/REAL and train/AI_MODIFIED
   to analyze frame composition (tight face crops vs full scenes).
"""

import os
import sys
import io
import json
import zipfile
import cv2
import numpy as np

# Force UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import create_app


def run_video_inspection():
    print("=" * 85)
    print(" 🎬 PART 1: EVALUATING REAL-WORLD USER VIDEO VIA /api/detect/video")
    print("=" * 85)

    video_path = os.path.join(current_dir, "uploads", "c9a84a5e0f3d_Video_Updated_to_Show_Hugging.mp4")
    if not os.path.exists(video_path):
        print(f"[!] Error: Video not found at {video_path}")
        return

    app = create_app("development")
    app.config["TESTING"] = True
    client = app.test_client()

    with open(video_path, "rb") as f:
        res = client.post(
            "/api/detect/video",
            data={"file": (f, "Video_Updated_to_Show_Hugging.mp4")},
            content_type="multipart/form-data"
        )

    if res.status_code != 200:
        print(f"[!] Request failed: HTTP {res.status_code} - {res.data.decode('utf-8')}")
        return

    data = json.loads(res.data)

    print("\n[*] FULL API RESPONSE JSON:")
    print(json.dumps(data, indent=2))

    meta = data.get("video_metadata", {})
    print("\n" + "-" * 85)
    print(" 📹 VIDEO METADATA SUMMARY:")
    print(f" * Resolution   : {meta.get('width')} x {meta.get('height')}")
    print(f" * FPS          : {meta.get('fps')}")
    print(f" * Total Frames : {meta.get('total_frames')}")
    print(f" * Duration     : {meta.get('duration_seconds')}s (Analyzed: {meta.get('analyzed_duration_seconds')}s)")
    print(f" * Sampled Count: {meta.get('sampled_frames_count')} frames")
    print(f" * Final Verdict: {data.get('verdict')} ({data.get('sub_type')}) - Conf: {data.get('confidence')}%")
    print(f" * Flagged Ratio: {data.get('flagged_ratio_pct')}% ({data.get('flagged_frames_count')}/{data.get('total_sampled_frames')} frames)")
    print("-" * 85)


def inspect_training_images():
    print("\n" + "=" * 85)
    print(" 🖼️ PART 2: INSPECTING TRAINING IMAGES (REAL vs AI_MODIFIED)")
    print("=" * 85)

    possible_dirs = [
        r"G:\My Drive\deepfake_project\datasets",
        os.path.abspath("datasets"),
        os.path.join(root_dir, "datasets"),
        r"C:\content\datasets"
    ]

    p3_path = None
    for d in possible_dirs:
        cand = os.path.join(d, "processed_3class.zip")
        if os.path.exists(cand):
            p3_path = cand
            break

    if not p3_path:
        print("[!] Error: processed_3class.zip not found.")
        return

    print(f"[*] Opening dataset zip: {p3_path}")
    zf = zipfile.ZipFile(p3_path, "r")
    namelist = zf.namelist()

    real_train = [n for n in namelist if "train/real" in n.lower() or "train/0_real" in n.lower() or "train/2_real" in n.lower() or "/real/" in n.lower()]
    mod_train = [n for n in namelist if "train/ai_modified" in n.lower() or "train/1_ai_modified" in n.lower() or "/ai_modified/" in n.lower() or "train/modified" in n.lower()]

    print(f"[*] Found {len(real_train)} REAL candidates, {len(mod_train)} AI_MODIFIED candidates in zip.")

    # Filter for image files
    real_imgs = [n for n in real_train if n.lower().endswith(('.jpg', '.jpeg', '.png'))][:5]
    mod_imgs = [n for n in mod_train if n.lower().endswith(('.jpg', '.jpeg', '.png'))][:5]

    sample_out_dir = os.path.join(current_dir, "sample_training_inspections")
    os.makedirs(sample_out_dir, exist_ok=True)

    # Face detector to measure face box area vs total image area
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def analyze_samples(img_names, label):
        print(f"\n--- 5 Sample Images from {label} ---")
        for i, name in enumerate(img_names):
            data = zf.read(name)
            nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            h, w, c = img.shape
            
            # Detect faces to quantify face-to-image ratio
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3)
            
            face_info = []
            if len(faces) > 0:
                for (fx, fy, fw, fh) in faces:
                    face_area_pct = (fw * fh) / (w * h) * 100
                    face_info.append(f"Face box: {fw}x{fh} ({face_area_pct:.1f}% of image area)")
            else:
                face_info.append("No frontal face detected by Haar (may be close crop of face features or profile)")

            out_filename = f"{label.lower()}_sample_{i+1}_{os.path.basename(name)}"
            out_filepath = os.path.join(sample_out_dir, out_filename)
            with open(out_filepath, "wb") as out_f:
                out_f.write(data)

            print(f" Sample #{i+1}: {name}")
            print(f"   ↳ Resolution: {w}x{h} | Aspect Ratio: {w/h:.2f} | {', '.join(face_info)}")
            print(f"   ↳ Saved to: {out_filepath}")

    analyze_samples(real_imgs, "REAL")
    analyze_samples(mod_imgs, "AI_MODIFIED")
    print("=" * 85)


if __name__ == "__main__":
    run_video_inspection()
    inspect_training_images()
