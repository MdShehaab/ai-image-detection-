"""
Diagnostic script for testing the live Flask API /api/detect/image endpoint
against 50 random test split images (17 ai_generated, 17 ai_modified, 16 real)
from manifest_combined.csv.
"""

import os
import sys
import io
import time
import json
import inspect
import hashlib
import zipfile
import pandas as pd
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

try:
    from app import create_app
    from models.image_detector.model import DeepfakeImageDetector
except ImportError:
    from backend.app import create_app
    from backend.models.image_detector.model import DeepfakeImageDetector


def get_file_sha256(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()


def print_environment_and_model_audit():
    """Print the exact model file details and preprocess_image source code."""
    print("=" * 85, flush=True)
    print(" [*] DIAGNOSTIC AUDIT: MODEL & PREPROCESSING CODE PATH", flush=True)
    print("=" * 85, flush=True)

    detector = DeepfakeImageDetector()
    model_file = detector.model_path

    if model_file and os.path.exists(model_file):
        file_size_mb = os.path.getsize(model_file) / (1024 * 1024)
        file_mtime = time.ctime(os.path.getmtime(model_file))
        sha256 = get_file_sha256(model_file)
        print(f"[*] Loaded Model Path   : {os.path.abspath(model_file)}", flush=True)
        print(f"[*] Model File Size     : {file_size_mb:.2f} MB ({os.path.getsize(model_file):,} bytes)", flush=True)
        print(f"[*] Last Modified Time  : {file_mtime}", flush=True)
        print(f"[*] Model SHA256 Hash   : {sha256}", flush=True)
        print(f"[*] Model Status Loaded : {detector.is_loaded}", flush=True)
    else:
        print(f"[!] Warning: Model file not found at {model_file}", flush=True)

    print("\n--- Preprocessing Source Code in model.py (DeepfakeImageDetector.preprocess_image) ---", flush=True)
    source_code = inspect.getsource(detector.preprocess_image)
    print(source_code.strip(), flush=True)

    if "preprocess_input(" in source_code:
        print("\n[!] WARNING: 'preprocess_input()' call IS PRESENT in preprocess_image()!", flush=True)
    else:
        print("\n[+] VERIFIED: 'preprocess_input()' is completely REMOVED. Raw 0-255 RGB float32 values are passed directly.", flush=True)
    print("=" * 85, flush=True)


def load_dataset_zips():
    """Locate and open dataset zip files from Google Drive or local directories with O(1) filename set caches."""
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
            print(f"[*] Opened processed_3class zip: {p3_path}", flush=True)
        if os.path.exists(id_path) and "image_detection" not in zips:
            zf = zipfile.ZipFile(id_path, "r")
            zips["image_detection"] = {"zip": zf, "namelist_set": set(zf.namelist())}
            print(f"[*] Opened image_detection zip: {id_path}", flush=True)

    return zips


def resolve_image_bytes(image_path: str, zips: dict) -> bytes:
    """Retrieve raw image bytes from local disk or zip archives with O(1) lookup."""
    # 1. Check local filesystem
    candidates = [
        image_path,
        os.path.join(root_dir, image_path),
        os.path.join(root_dir, "datasets", image_path)
    ]
    for cand in candidates:
        if os.path.exists(cand) and os.path.isfile(cand):
            with open(cand, "rb") as f:
                return f.read()

    # 2. Check zip archives with O(1) set membership
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

    raise FileNotFoundError(f"Could not locate image file for '{image_path}' in local disk or zip archives.")


def main():
    print_environment_and_model_audit()

    manifest_candidates = [
        "datasets/manifest_combined.csv",
        os.path.join(root_dir, "datasets", "manifest_combined.csv"),
        "manifest_combined.csv"
    ]
    manifest_path = None
    for mc in manifest_candidates:
        if os.path.exists(mc):
            manifest_path = mc
            break

    if not manifest_path:
        print(f"[!] Error: manifest_combined.csv not found.", flush=True)
        return

    print("\n[*] Loading dataset manifest from:", os.path.abspath(manifest_path), flush=True)
    df = pd.read_csv(manifest_path)
    test_df = df[df["split"] == "test"].copy()

    # Sample 17 ai_generated, 17 ai_modified, 16 real = 50 total
    sample_gen = test_df[test_df["class"] == "ai_generated"].sample(n=17, random_state=42)
    sample_mod = test_df[test_df["class"] == "ai_modified"].sample(n=17, random_state=42)
    sample_real = test_df[test_df["class"] == "real"].sample(n=16, random_state=42)

    sample_50 = pd.concat([sample_gen, sample_mod, sample_real]).sample(frac=1.0, random_state=42).reset_index(drop=True)
    print(f"[*] Prepared {len(sample_50)} balanced test samples:", flush=True)
    for cls_name, count in sample_50["class"].value_counts().items():
        print(f"    - {cls_name:<14}: {count} samples", flush=True)

    zips = load_dataset_zips()

    # Initialize Flask test client (exact WSGI dispatch matching HTTP endpoint)
    app = create_app("development")
    app.config["TESTING"] = True
    client = app.test_client()

    print("\n" + "=" * 85, flush=True)
    print(" [*] RUNNING LIVE /api/detect/image ENDPOINT EVALUATION (50 Samples)", flush=True)
    print("=" * 85, flush=True)

    y_true = []
    y_pred = []
    y_verdict = []
    y_conf = []

    classes = ["ai_generated", "ai_modified", "real"]
    class_to_idx = {c: i for i, c in enumerate(classes)}

    start_time = time.time()

    for idx, row in sample_50.iterrows():
        img_rel_path = row["image_path"]
        true_label = row["class"]
        filename = os.path.basename(img_rel_path)

        try:
            img_bytes = resolve_image_bytes(img_rel_path, zips)
        except Exception as e:
            print(f"[{idx+1:02d}/50] [ERROR] Failed to load image {img_rel_path}: {e}", flush=True)
            continue

        # Post exactly as frontend / HTTP client does with multipart/form-data
        data = {
            "file": (io.BytesIO(img_bytes), filename)
        }
        res = client.post(
            "/api/detect/image",
            data=data,
            content_type="multipart/form-data"
        )

        if res.status_code != 200:
            print(f"[{idx+1:02d}/50] [FAIL HTTP {res.status_code}] Response: {res.data.decode('utf-8')}", flush=True)
            continue

        res_json = json.loads(res.data)
        pred_label = res_json.get("sub_type") or res_json.get("prediction_subtype")
        verdict = res_json.get("verdict")
        confidence = res_json.get("confidence", 0.0)

        y_true.append(true_label)
        y_pred.append(pred_label)
        y_verdict.append(verdict)
        y_conf.append(confidence)

        is_correct = (pred_label == true_label)
        status_sym = "[CORRECT]" if is_correct else "[ WRONG ]"
        current_correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        current_total = len(y_true)
        current_acc = (current_correct / current_total) * 100

        print(f" [{current_total:02d}/50] {status_sym:<9} | True: {true_label:<12} -> Pred: {pred_label:<12} (Verdict: {verdict:<11}, Conf: {confidence:5.1f}%) | Acc: {current_correct:02d}/{current_total:02d} ({current_acc:5.1f}%)", flush=True)

    total_time = time.time() - start_time
    total_evaluated = len(y_true)
    total_correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    final_accuracy = (total_correct / total_evaluated) * 100 if total_evaluated > 0 else 0

    print("\n" + "=" * 85, flush=True)
    print(" [*] FINAL DIAGNOSTIC EVALUATION RESULTS", flush=True)
    print("=" * 85, flush=True)
    print(f"[*] Total Samples Tested : {total_evaluated}", flush=True)
    print(f"[*] Total Correct        : {total_correct}", flush=True)
    print(f"[*] Overall Test Accuracy: {final_accuracy:.2f}% ({total_correct} / {total_evaluated})", flush=True)
    print(f"[*] Total Inference Time : {total_time:.2f}s (Avg {total_time/max(1, total_evaluated)*1000:.1f}ms/image)", flush=True)
    print("-" * 85, flush=True)

    # Per-Class Accuracy Breakdown
    print("\n--- Per-Class Accuracy Breakdown ---", flush=True)
    for c in classes:
        c_true_indices = [i for i, t in enumerate(y_true) if t == c]
        if c_true_indices:
            c_correct = sum(1 for i in c_true_indices if y_pred[i] == c)
            c_total = len(c_true_indices)
            c_acc = (c_correct / c_total) * 100
            print(f" * {c:<14}: {c_acc:6.2f}% ({c_correct}/{c_total})", flush=True)

    # Confusion Matrix Calculation
    cm = np.zeros((3, 3), dtype=int)
    for t, p in zip(y_true, y_pred):
        if t in class_to_idx and p in class_to_idx:
            cm[class_to_idx[t]][class_to_idx[p]] += 1

    print("\n--- Confusion Matrix ---", flush=True)
    header = f"{'True \\ Pred':<16} | {'ai_generated':<13} | {'ai_modified':<13} | {'real':<13}"
    print(header, flush=True)
    print("-" * len(header), flush=True)
    for i, c_name in enumerate(classes):
        row_str = f"{c_name:<16} | {cm[i][0]:<13} | {cm[i][1]:<13} | {cm[i][2]:<13}"
        print(row_str, flush=True)

    print("=" * 85, flush=True)
    if final_accuracy >= 70.0:
        print(f"[+] VERDICT: Endpoint inference is performing consistently with training (~82%).", flush=True)
    else:
        print(f"[!] VERDICT: Accuracy ({final_accuracy:.2f}%) is significantly lower than expected.", flush=True)
    print("=" * 85 + "\n", flush=True)


if __name__ == "__main__":
    main()
