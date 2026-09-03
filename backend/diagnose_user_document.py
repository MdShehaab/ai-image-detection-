"""
Full Forensic Diagnostic Script for User Uploaded Document (myjpg.jpg).
Performs in-depth analysis of:
1. OCR / Morphological text region segmentation quality (over vs under segmentation).
2. Per-region tamper scores, stroke widths, and forensic metrics for ALL detected fields.
3. JPEG quantization tables, chroma subsampling, and estimated quality level.
4. ELA intensity map statistics (min/max/mean/std) compared against clean scanned baseline.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List, Tuple
import cv2
import numpy as np
from PIL import Image, JpegImagePlugin

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

from models.document_detector.model import DocumentForgeryDetector
from test_document_forgery import create_genuine_scanned_letter


def estimate_jpeg_quality(pil_img: Image.Image) -> Dict[str, Any]:
    """Inspect JPEG quantization tables and estimate original quality factor."""
    info = {
        "format": pil_img.format,
        "mode": pil_img.mode,
        "size": pil_img.size,
        "has_quantization_tables": False,
        "estimated_quality": "Unknown / Non-JPEG",
        "chroma_subsampling": "Unknown"
    }

    if hasattr(pil_img, "quantization") and pil_img.quantization:
        info["has_quantization_tables"] = True
        q_tables = pil_img.quantization
        # Luminance table is table 0
        if 0 in q_tables:
            luma_q = list(q_tables[0])
            # Approximation of quality factor from luminance table mean
            luma_mean = float(np.mean(luma_q))
            # Lower quantization values = higher quality
            estimated_q = max(1, min(100, int(100 - luma_mean * 1.5)))
            info["estimated_quality"] = f"~{estimated_q}% (Luma Mean: {luma_mean:.1f})"
            info["luma_quantization_table_first_8"] = luma_q[:8]

    # Check chroma subsampling
    if hasattr(pil_img, "layer"):
        info["chroma_subsampling"] = str(pil_img.layer)
    if "subsampling" in pil_img.info:
        info["chroma_subsampling"] = str(pil_img.info["subsampling"])

    return info


def run_full_diagnostic():
    user_doc_path = os.path.join(current_dir, "uploads", "38e2491d493e_myjpg.jpg")
    if not os.path.exists(user_doc_path):
        user_doc_path = os.path.join(current_dir, "uploads", "60903fa43dd4_myjpg.jpg")

    if not os.path.exists(user_doc_path):
        print(f"[!] User document not found in uploads.")
        return

    print("=" * 90)
    print(f" 🔬 DEEP FORENSIC DIAGNOSTIC AUDIT: {os.path.basename(user_doc_path)}")
    print("=" * 90)

    # 1. JPEG Compression & Metadata Inspection
    pil_img = Image.open(user_doc_path)
    file_size_kb = os.path.getsize(user_doc_path) / 1024.0
    w, h = pil_img.size
    q_info = estimate_jpeg_quality(pil_img)

    print("\n--- 1. JPEG COMPRESSION & METADATA AUDIT ---")
    print(f" * File Size           : {file_size_kb:.2f} KB ({os.path.getsize(user_doc_path):,} bytes)")
    print(f" * Resolution          : {w} x {h} pixels ({w*h:,} total pixels)")
    print(f" * Bits Per Pixel (BPP): {(os.path.getsize(user_doc_path) * 8) / (w * h):.3f} bits/pixel")
    print(f" * Estimated Quality   : {q_info['estimated_quality']}")
    print(f" * Chroma Subsampling  : {q_info['chroma_subsampling']}")
    print(f" * EXIF Header Present : {bool(pil_img.getexif())}")
    
    if file_size_kb < 60.0 and (w * h) > 400000:
        print(" [!] NOTE: Low file size relative to pixel resolution indicates heavy social media / WhatsApp compression re-encoding.")

    # 2. Document Detector Pipeline Execution
    detector = DocumentForgeryDetector(tamper_threshold=0.65)
    img_bgr, meta = detector.load_document_image(user_doc_path)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Text Segmentation
    candidate_regions = detector.segment_text_regions(img_bgr)
    ela_map = detector.compute_ela_map(img_bgr, quality=85)
    noise_map = detector.compute_noise_map(gray)

    print("\n--- 2. OCR & TEXT REGION SEGMENTATION ANALYSIS ---")
    print(f" * Total Candidate Regions Detected : {len(candidate_regions)}")
    
    # Check bounding box distribution (size, aspect ratio)
    areas = [r["area"] for r in candidate_regions]
    widths = [r["bbox"][2] for r in candidate_regions]
    heights = [r["bbox"][3] for r in candidate_regions]
    
    print(f" * Region Width Range               : {min(widths)}px to {max(widths)}px (Median: {np.median(widths):.1f}px)")
    print(f" * Region Height Range              : {min(heights)}px to {max(heights)}px (Median: {np.median(heights):.1f}px)")
    print(f" * Total Bounding Box Area Coverage : {sum(areas) / (w * h) * 100:.2f}% of page")

    # 3. Baseline Statistics & Feature Extraction
    region_features = []
    for reg in candidate_regions:
        feats = detector.analyze_region_features(img_bgr, gray, ela_map, noise_map, reg["bbox"])
        region_features.append(feats)

    text_feats = [f for reg, f in zip(candidate_regions, region_features) if not reg.get("is_graphic_stamp")]
    if not text_feats:
        text_feats = region_features

    stroke_widths = [f["stroke_width"] for f in text_feats]
    edge_sharpnesses = [f["edge_sharpness"] for f in text_feats]
    ela_intensities = [f["ela_intensity"] for f in text_feats]
    noise_variances = [f["noise_variance"] for f in text_feats]

    med_stroke = float(np.median(stroke_widths))
    iqr_stroke = max(0.5, float(np.percentile(stroke_widths, 75) - np.percentile(stroke_widths, 25)))
    med_sharp = float(np.median(edge_sharpnesses))
    iqr_sharp = max(8.0, float(np.percentile(edge_sharpnesses, 75) - np.percentile(edge_sharpnesses, 25)))
    med_ela = float(np.median(ela_intensities))
    iqr_ela = max(0.8, float(np.percentile(ela_intensities, 75) - np.percentile(ela_intensities, 25)))
    med_noise = float(np.median(noise_variances))
    iqr_noise = max(1.0, float(np.percentile(noise_variances, 75) - np.percentile(noise_variances, 25)))

    print("\n--- 3. DOCUMENT-WIDE BASELINE FORENSIC METRICS ---")
    print(f" * Median Font Stroke Width : {med_stroke:.2f}px (IQR: {iqr_stroke:.2f}px)")
    print(f" * Median Edge Sharpness    : {med_sharp:.2f} (IQR: {iqr_sharp:.2f})")
    print(f" * Median ELA Intensity     : {med_ela:.2f} (IQR: {iqr_ela:.2f})")
    print(f" * Median Noise Variance    : {med_noise:.2f} (IQR: {iqr_noise:.2f})")

    # 4. Per-Region Scores Table (ALL Regions)
    print("\n--- 4. PER-REGION TAMPER SCORES & METRICS (ALL REGIONS) ---")
    header = f"{'Region #':<9} | {'BBox (x, y, w, h)':<22} | {'Stroke':<8} | {'Sharpness':<10} | {'ELA':<6} | {'Noise':<6} | {'Tamper Score':<13} | {'Status':<10}"
    print(header)
    print("-" * len(header))

    ranked_regions = []
    for idx, (reg, f) in enumerate(zip(candidate_regions, region_features)):
        bbox = reg["bbox"]
        bx, by, bw, bh = bbox
        is_stamp = reg.get("is_graphic_stamp", False)

        dev_stroke = abs(f["stroke_width"] - med_stroke) / iqr_stroke
        dev_sharp = abs(f["edge_sharpness"] - med_sharp) / iqr_sharp
        dev_contrast = abs(f["contrast"] - 0.5) / 0.15
        font_anomaly = min(1.0, (dev_stroke * 0.55 + dev_sharp * 0.30 + dev_contrast * 0.15) / 3.2)
        dev_ela = max(0.0, (f["ela_intensity"] - med_ela) / iqr_ela)
        ela_anomaly = min(1.0, dev_ela / 3.0)
        dev_noise = abs(f["noise_variance"] - med_noise) / iqr_noise
        noise_anomaly = min(1.0, dev_noise / 3.0)

        tamper_score = round(float(0.50 * font_anomaly + 0.30 * ela_anomaly + 0.20 * noise_anomaly), 3)
        status = "FLAGGED [!]" if tamper_score >= 0.65 else "Normal"

        ranked_regions.append({
            "idx": idx + 1,
            "bbox": bbox,
            "stroke": f["stroke_width"],
            "sharp": f["edge_sharpness"],
            "ela": f["ela_intensity"],
            "noise": f["noise_variance"],
            "tamper_score": tamper_score,
            "status": status
        })

        print(f"Region #{idx+1:<2} | [{bx:3d}, {by:3d}, {bw:3d}, {bh:3d}]       | {f['stroke_width']:5.2f}px | {f['edge_sharpness']:9.2f} | {f['ela_intensity']:5.2f} | {f['noise_variance']:5.2f} | {tamper_score*100:6.1f}%       | {status:<10}")

    # Top 5 most suspicious regions
    ranked_regions.sort(key=lambda r: r["tamper_score"], reverse=True)
    print("\n--- TOP 5 HIGHEST ANOMALY REGIONS ---")
    for tr in ranked_regions[:5]:
        print(f" * Region #{tr['idx']:02d} at {tr['bbox']}: Tamper Score = {tr['tamper_score']*100:.1f}% (Stroke: {tr['stroke']:.2f}px, ELA: {tr['ela']:.2f}, Noise: {tr['noise']:.2f})")

    # 5. ELA Signal Comparison: Uploaded Document vs Clean Scanned Document
    clean_test_path = "temp_clean_baseline.jpg"
    create_genuine_scanned_letter(clean_test_path)
    clean_bgr = cv2.imread(clean_test_path)
    clean_ela = detector.compute_ela_map(clean_bgr, quality=85)
    clean_gray = cv2.cvtColor(clean_bgr, cv2.COLOR_BGR2GRAY)
    clean_noise = detector.compute_noise_map(clean_gray)

    print("\n" + "=" * 90)
    print(" 📊 5. ELA & NOISE COMPARISON: USER DOCUMENT vs CLEAN SCANNED BASELINE")
    print("=" * 90)
    print(f"{'Metric':<30} | {'User Document (myjpg.jpg)':<26} | {'Clean Scanned Baseline':<26}")
    print("-" * 90)
    print(f"{'ELA Map Min / Max':<30} | {float(np.min(ela_map)):.1f} / {float(np.max(ela_map)):.1f}                     | {float(np.min(clean_ela)):.1f} / {float(np.max(clean_ela)):.1f}")
    print(f"{'ELA Map Mean':<30} | {float(np.mean(ela_map)):.2f}                       | {float(np.mean(clean_ela)):.2f}")
    print(f"{'ELA Map Std Dev':<30} | {float(np.std(ela_map)):.2f}                       | {float(np.std(clean_ela)):.2f}")
    print(f"{'Noise Map Mean':<30} | {float(np.mean(noise_map)):.2f}                       | {float(np.mean(clean_noise)):.2f}")
    print(f"{'Noise Map Std Dev':<30} | {float(np.std(noise_map)):.2f}                       | {float(np.std(clean_noise)):.2f}")
    print("=" * 90 + "\n")

    if os.path.exists(clean_test_path):
        os.remove(clean_test_path)


if __name__ == "__main__":
    run_full_diagnostic()
