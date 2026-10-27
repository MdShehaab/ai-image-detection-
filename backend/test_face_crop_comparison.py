"""
[EXPERIMENTAL] Face-Crop Comparison Test Script
================================================
Re-tests real photos from this session with both standard (no-crop) and
MTCNN face-crop preprocessing modes side-by-side.

Usage:
    cd backend
    python test_face_crop_comparison.py

The script:
  1. Finds the 3 "failing" real photos from the uploads directory (images
     uploaded during this session that a human face).
  2. Runs predict(compare_face_crop=True) on each.
  3. Reports verdict changes, confidence deltas, and crop status.
"""

import os
import sys
import json
import time

# Ensure backend modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Force UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from models.image_detector.model import DeepfakeImageDetector


# ---------------------------------------------------------------------------
# Test images — real photos that were tested through the API in this session
# The uploads folder keeps the last-saved copy under a uuid-prefixed filename.
# We also check the user's Downloads folder for the originals.
# ---------------------------------------------------------------------------

CANDIDATE_REAL_PHOTOS = [
    # Uploads folder (session copies)
    os.path.join(current_dir, "uploads", "a40e90bd3124_shehaab.jpg"),
    os.path.join(current_dir, "uploads", "6e2c3728583f_1.jpg"),
    os.path.join(current_dir, "uploads", "cf8c10b57529_download_2.jpg"),
    # Downloads originals (fallback)
    r"C:\Users\sheha\Downloads\shehaab.jpg",
    r"C:\Users\sheha\Downloads\1.jpg",
    r"C:\Users\sheha\Downloads\download (2).jpg",
    # WhatsApp/camera photos
    r"C:\Users\sheha\Downloads\WhatsApp Image 2026-09-29 at 9.32.56 AM.jpeg",
    r"C:\Users\sheha\Downloads\WhatsApp Image 2026-09-28 at 6.00.13 AM.jpeg",
    r"C:\Users\sheha\Downloads\WhatsApp Image 2026-09-28 at 6.00.14 AM.jpeg",
]


def verdict_icon(verdict: str) -> str:
    return "✅ REAL" if verdict == "REAL" else "❌ AI-MODIFIED"


def delta_str(no_crop_conf: float, face_crop_conf: float, no_verdict: str, fc_verdict: str) -> str:
    changed = no_verdict != fc_verdict
    delta = face_crop_conf - no_crop_conf
    sign = "+" if delta >= 0 else ""
    tag = " <<< VERDICT CHANGED" if changed else ""
    return f"Δconf={sign}{delta:.2f}%{tag}"


def run_comparison():
    print("=" * 80)
    print(" [EXPERIMENTAL] MTCNN FACE-CROP vs FULL-IMAGE INFERENCE COMPARISON")
    print("=" * 80)

    detector = DeepfakeImageDetector()

    if not detector.is_loaded:
        print("[WARN] Model weights NOT loaded — results will be stub/mock values.")
        print("       Make sure the Flask backend has been started at least once so")
        print("       model.keras / smoke_test.keras is present in weights/.\n")
    else:
        print(f"[INFO] Model loaded: {detector.model_path}\n")

    # Collect only files that actually exist
    test_photos = []
    seen = set()
    for p in CANDIDATE_REAL_PHOTOS:
        ap = os.path.abspath(p)
        if os.path.exists(ap) and ap not in seen:
            test_photos.append(ap)
            seen.add(ap)
        if len(test_photos) >= 3:
            break

    if not test_photos:
        print("[ERROR] No test photos found. Please ensure the uploaded photos exist in:")
        for p in CANDIDATE_REAL_PHOTOS[:3]:
            print(f"  - {p}")
        return

    print(f"[INFO] Testing {len(test_photos)} real photo(s):\n")
    for p in test_photos:
        print(f"  - {p}")
    print()

    results_summary = []

    for idx, photo_path in enumerate(test_photos, 1):
        fname = os.path.basename(photo_path)
        print(f"{'─'*80}")
        print(f" Photo {idx}/{len(test_photos)}: {fname}")
        print(f"{'─'*80}")

        t0 = time.time()
        result = detector.predict(photo_path, compare_face_crop=True)
        elapsed = round((time.time() - t0) * 1000, 1)

        no_crop  = result.get("no_crop", {})
        face_crop = result.get("face_crop", {})

        nc_verdict = no_crop.get("verdict", "N/A")
        nc_conf    = no_crop.get("confidence", 0.0)
        nc_prob_r  = no_crop.get("probabilities", {}).get("real", 0.0)
        nc_prob_f  = no_crop.get("probabilities", {}).get("fake", 0.0)

        fc_verdict = face_crop.get("verdict", "N/A")
        fc_conf    = face_crop.get("confidence", 0.0)
        fc_prob_r  = face_crop.get("probabilities", {}).get("real", 0.0)
        fc_prob_f  = face_crop.get("probabilities", {}).get("fake", 0.0)
        fc_status  = face_crop.get("crop_status", "unknown")

        verdict_changed = nc_verdict != fc_verdict

        print(f"\n  MODE          | VERDICT              | CONFIDENCE  | P(real)  | P(fake)")
        print(f"  {'─'*70}")
        print(f"  No-Crop       | {verdict_icon(nc_verdict):<20} | {nc_conf:>8.2f}%  | {nc_prob_r:.4f}  | {nc_prob_f:.4f}")
        print(f"  Face-Crop [X] | {verdict_icon(fc_verdict):<20} | {fc_conf:>8.2f}%  | {fc_prob_r:.4f}  | {fc_prob_f:.4f}")
        print(f"\n  Crop Status   : {fc_status}")
        print(f"  Verdict Change: {'YES  <<<' if verdict_changed else 'No'}")
        print(f"  Conf Delta    : {delta_str(nc_conf, fc_conf, nc_verdict, fc_verdict)}")
        print(f"  Total Time    : {elapsed} ms\n")

        results_summary.append({
            "photo": fname,
            "no_crop_verdict": nc_verdict,
            "face_crop_verdict": fc_verdict,
            "verdict_changed": verdict_changed,
            "no_crop_confidence": nc_conf,
            "face_crop_confidence": fc_conf,
            "no_crop_p_real": nc_prob_r,
            "face_crop_p_real": fc_prob_r,
            "crop_status": fc_status,
        })

    # Final summary table
    print(f"\n{'='*80}")
    print(" SUMMARY TABLE")
    print(f"{'='*80}")
    print(f"  {'Photo':<35} | {'No-Crop':<12} | {'Face-Crop':<12} | {'Changed?':<10} | Δ P(real)")
    print(f"  {'─'*85}")
    any_changed = False
    for r in results_summary:
        delta_r = r["face_crop_p_real"] - r["no_crop_p_real"]
        sign = "+" if delta_r >= 0 else ""
        changed_str = "YES <<<" if r["verdict_changed"] else "No"
        if r["verdict_changed"]:
            any_changed = True
        print(f"  {r['photo']:<35} | {r['no_crop_verdict']:<12} | {r['face_crop_verdict']:<12} | {changed_str:<10} | {sign}{delta_r:.4f}")

    print(f"\n  Photos tested : {len(results_summary)}")
    print(f"  Verdict changes from face-crop : {sum(1 for r in results_summary if r['verdict_changed'])}")
    if any_changed:
        print("\n  [!] Face-crop DID change at least one verdict.")
        print("      Consider enabling face-crop mode for portrait/selfie uploads.")
    else:
        print("\n  [✓] Face-crop did NOT change any verdicts on these photos.")
        print("      The model's bias applies equally to face-region crops.")

    print(f"\n{'='*80}\n")

    # Save results to JSON
    out_path = os.path.join(current_dir, "..", "reports", "face_crop_comparison.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print(f"[INFO] Full results saved to: {os.path.abspath(out_path)}")


if __name__ == "__main__":
    run_comparison()
