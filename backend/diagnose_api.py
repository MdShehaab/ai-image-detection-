"""
Diagnostic script for testing the live Flask API /api/detect/image endpoint
against 50 random test split images (17 ai_generated, 17 ai_modified, 16 real)
from manifest_combined.csv at multiple decision thresholds: 0.50, 0.60, 0.70, 0.80, 0.85.
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
        print(f"[*] Default FAKE_THRESH : {detector.fake_threshold}", flush=True)
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

    raise FileNotFoundError(f"Could not locate image file for '{image_path}' in local disk or zip archives.")


def evaluate_threshold(results_data: list, threshold: float):
    """Evaluate accuracy and confusion matrix for a specific FAKE_THRESHOLD."""
    classes = ["ai_generated", "ai_modified", "real"]
    class_to_idx = {c: i for i, c in enumerate(classes)}

    y_true = []
    y_pred = []
    y_verdict = []

    for item in results_data:
        true_label = item["true_label"]
        probs = item["probabilities"]

        p_gen = probs["ai_generated"]
        p_mod = probs["ai_modified"]
        p_real = probs["real"]
        fake_prob = p_gen + p_mod

        if fake_prob >= threshold:
            pred_label = "ai_generated" if p_gen > p_mod else "ai_modified"
            verdict = "AI-MODIFIED"
        else:
            pred_label = "real"
            verdict = "REAL"

        y_true.append(true_label)
        y_pred.append(pred_label)
        y_verdict.append(verdict)

    total_evaluated = len(y_true)
    total_correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    acc = (total_correct / total_evaluated) * 100 if total_evaluated > 0 else 0

    print("\n" + "=" * 85, flush=True)
    print(f" 📊 RESULTS FOR FAKE_THRESHOLD = {threshold:.2f} ({int(threshold*100)}% Confidence Required to Flag Fake)", flush=True)
    print("=" * 85, flush=True)
    print(f"[*] Overall Test Accuracy : {acc:.2f}% ({total_correct} / {total_evaluated})", flush=True)
    print("-" * 85, flush=True)

    # Per-Class Breakdown
    print("--- Per-Class Recall / Accuracy Breakdown ---", flush=True)
    class_stats = {}
    for c in classes:
        c_true_indices = [i for i, t in enumerate(y_true) if t == c]
        if c_true_indices:
            c_correct = sum(1 for i in c_true_indices if y_pred[i] == c)
            c_total = len(c_true_indices)
            c_acc = (c_correct / c_total) * 100
            class_stats[c] = (c_correct, c_total, c_acc)
            print(f" * {c:<14}: {c_acc:6.2f}% ({c_correct:02d}/{c_total:02d} correct)", flush=True)

    # Confusion Matrix
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

    return {
        "threshold": threshold,
        "accuracy": acc,
        "total_correct": total_correct,
        "total": total_evaluated,
        "class_stats": class_stats,
        "cm": cm,
        "y_pred": y_pred
    }


def analyze_misclassified_reals(collected_results: list):
    """Analyze the exact calibrated and raw probabilities for real images misclassified at threshold 0.70."""
    print("\n" + "=" * 85, flush=True)
    print(" 🔬 IN-DEPTH ANALYSIS: REAL SAMPLES MISCLASSIFIED AS AI-MODIFIED AT THRESHOLD 0.70", flush=True)
    print("=" * 85, flush=True)

    real_samples = [item for item in collected_results if item["true_label"] == "real"]
    flagged_reals = []

    for item in real_samples:
        probs = item["probabilities"]
        p_gen = probs["ai_generated"]
        p_mod = probs["ai_modified"]
        p_real = probs["real"]
        fake_prob = p_gen + p_mod

        if fake_prob >= 0.70:
            flagged_reals.append((item, fake_prob, p_gen, p_mod, p_real))

    print(f"[*] Total REAL Samples in Test Slice: {len(real_samples)}")
    print(f"[*] Correctly Identified as REAL     : {len(real_samples) - len(flagged_reals)} / {len(real_samples)}")
    print(f"[*] Flagged as AI-MODIFIED (at 0.70) : {len(flagged_reals)} / {len(real_samples)}\n", flush=True)

    header = f"{'Sample':<10} | {'Filename':<24} | {'Fake Prob':<10} | {'p(mod)':<9} | {'p(real)':<9} | {'At 0.70':<9} | {'At 0.80':<9} | {'At 0.85':<9}"
    print(header, flush=True)
    print("-" * len(header), flush=True)

    for item, fake_prob, p_gen, p_mod, p_real in flagged_reals:
        idx = item["idx"]
        fn = item["filename"]
        raw = item["raw_probabilities"]

        pred_070 = "AI-MOD" if fake_prob >= 0.70 else "REAL"
        pred_080 = "AI-MOD" if fake_prob >= 0.80 else "REAL"
        pred_085 = "AI-MOD" if fake_prob >= 0.85 else "REAL"

        print(f"Sample #{idx:02d} | {fn:<24} | {fake_prob*100:6.2f}%   | {p_mod*100:6.2f}% | {p_real*100:6.2f}% | {pred_070:<9} | {pred_080:<9} | {pred_085:<9}", flush=True)
        print(f"   ↳ [Raw Softmax]: gen={raw.get('ai_generated',0)*100:5.2f}%, mod={raw.get('ai_modified',0)*100:5.2f}%, real={raw.get('real',0)*100:5.2f}%", flush=True)

    # Distribution clustering summary
    fake_probs = [fp for _, fp, _, _, _ in flagged_reals]
    above_85 = sum(1 for fp in fake_probs if fp >= 0.85)
    between_70_85 = sum(1 for fp in fake_probs if 0.70 <= fp < 0.85)
    
    print("\n--- Distribution Clustering Summary of the 8 Flagged Real Images ---", flush=True)
    print(f" * Clustered between 70.0% - 85.0% : {between_70_85} / {len(flagged_reals)} samples", flush=True)
    print(f" * High Confidence (>= 85.0%)     : {above_85} / {len(flagged_reals)} samples (avg confidence: {np.mean(fake_probs)*100:.2f}%)", flush=True)
    print("=" * 85 + "\n", flush=True)


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
    print(" [*] SENDING 50 SAMPLES THROUGH LIVE /api/detect/image ENDPOINT", flush=True)
    print("=" * 85, flush=True)

    collected_results = []
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
        probs = res_json.get("probabilities", {})

        collected_results.append({
            "idx": idx + 1,
            "filename": filename,
            "true_label": true_label,
            "image_path": img_rel_path,
            "probabilities": probs,
            "raw_probabilities": res_json.get("raw_probabilities", {})
        })

        p_gen = probs.get("ai_generated", 0.0)
        p_mod = probs.get("ai_modified", 0.0)
        p_real = probs.get("real", 0.0)
        print(f" [{idx+1:02d}/50] True: {true_label:<12} | Calibrated Probs -> Gen: {p_gen*100:5.1f}%, Mod: {p_mod*100:5.1f}%, Real: {p_real*100:5.1f}% (Fake Total: {(p_gen+p_mod)*100:5.1f}%)", flush=True)

    total_time = time.time() - start_time
    print(f"\n[*] All 50 API inferences completed in {total_time:.2f}s (Avg {total_time/len(collected_results)*1000:.1f}ms/image)")

    # Evaluate across all requested thresholds
    thresholds = [0.50, 0.60, 0.70, 0.80, 0.85]
    eval_results = []
    for th in thresholds:
        eval_results.append(evaluate_threshold(collected_results, threshold=th))

    # Comprehensive Comparison Matrix Table
    print("\n" + "=" * 85, flush=True)
    print(" 🏆 THRESHOLD COMPARISON MATRIX (0.50 vs 0.60 vs 0.70 vs 0.80 vs 0.85)", flush=True)
    print("=" * 85, flush=True)
    print(f"{'Threshold':<12} | {'Overall Acc':<14} | {'ai_generated':<15} | {'ai_modified':<15} | {'real Recall':<15}", flush=True)
    print("-" * 85, flush=True)
    for ev in eval_results:
        t = ev["threshold"]
        o_acc = ev["accuracy"]
        gen_acc = ev["class_stats"]["ai_generated"][2]
        mod_acc = ev["class_stats"]["ai_modified"][2]
        real_acc = ev["class_stats"]["real"][2]
        print(f"{t:<12.2f} | {o_acc:5.2f}% ({ev['total_correct']}/{ev['total']})   | {gen_acc:5.2f}% ({ev['class_stats']['ai_generated'][0]}/{ev['class_stats']['ai_generated'][1]})    | {mod_acc:5.2f}% ({ev['class_stats']['ai_modified'][0]}/{ev['class_stats']['ai_modified'][1]})    | {real_acc:5.2f}% ({ev['class_stats']['real'][0]}/{ev['class_stats']['real'][1]})", flush=True)
    print("=" * 85, flush=True)

    # Detailed Inspection of the 8 Real images
    analyze_misclassified_reals(collected_results)


if __name__ == "__main__":
    main()
