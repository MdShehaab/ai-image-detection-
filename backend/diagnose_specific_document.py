"""
Comprehensive Diagnostic Script for Document Image Analysis (pp.jpg / po.jpeg / myjpg.jpg).
Answers all 4 points:
1. Exact number of detected OCR/morphological text regions and segmentation quality.
2. Per-region tamper scores, stroke widths, and metrics for ALL regions.
3. Actual JPEG quality, quantization tables, and compression metadata.
4. ELA intensity map statistics (min, max, mean, std) vs clean scanned document.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List, Tuple
import cv2
import numpy as np
from PIL import Image

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from models.document_detector.model import DocumentForgeryDetector
from test_document_forgery import create_genuine_scanned_letter


def get_jpeg_info(img_path: str) -> Dict[str, Any]:
    """Inspect JPEG quantization tables, chroma subsampling, and estimate quality level."""
    pil_img = Image.open(img_path)
    file_size = os.path.getsize(img_path)
    w, h = pil_img.size
    
    info = {
        "file_name": os.path.basename(img_path),
        "file_size_kb": round(file_size / 1024.0, 2),
        "resolution": f"{w} x {h}",
        "total_pixels": w * h,
        "bits_per_pixel": round((file_size * 8) / (w * h), 3),
        "format": pil_img.format,
        "has_exif": bool(pil_img.getexif()),
        "estimated_quality": "Unknown",
        "luma_mean_quant": 0.0,
        "chroma_mean_quant": 0.0,
        "subsampling": "Standard / Unknown"
    }

    if hasattr(pil_img, "quantization") and pil_img.quantization:
        q_tables = pil_img.quantization
        if 0 in q_tables:
            luma_q = list(q_tables[0])
            luma_mean = float(np.mean(luma_q))
            info["luma_mean_quant"] = round(luma_mean, 2)
            # High quality JPEGs (Q >= 90) have luma_mean <= 3.0
            # Medium quality JPEGs (Q 70-85) have luma_mean 5.0 - 15.0
            # Low quality (Q <= 60 / WhatsApp) have luma_mean > 20.0
            est_q = max(1, min(100, int(100 - luma_mean * 1.6)))
            info["estimated_quality"] = f"~{est_q}% (Luma Quant Mean: {luma_mean:.1f})"
            info["luma_quant_sample"] = luma_q[:8]
        if 1 in q_tables:
            chroma_q = list(q_tables[1])
            info["chroma_mean_quant"] = round(float(np.mean(chroma_q)), 2)

    return info


def analyze_target_document(target_path: str):
    print("=" * 95)
    print(f" 🔬 FORENSIC AUDIT: {os.path.basename(target_path)}")
    print("=" * 95)

    # 1. JPEG Compression Analysis
    q_info = get_jpeg_info(target_path)
    print("\n--- 1. JPEG COMPRESSION & METADATA AUDIT ---")
    print(f" * File Name               : {q_info['file_name']}")
    print(f" * File Size               : {q_info['file_size_kb']} KB ({os.path.getsize(target_path):,} bytes)")
    print(f" * Native Resolution       : {q_info['resolution']} ({q_info['total_pixels']:,} px)")
    print(f" * Bits Per Pixel (BPP)    : {q_info['bits_per_pixel']} bpp")
    print(f" * Estimated JPEG Quality  : {q_info['estimated_quality']}")
    print(f" * Luma Quantization Mean  : {q_info['luma_mean_quant']} (Higher = heavier compression loss)")
    print(f" * Chroma Quantization Mean: {q_info['chroma_mean_quant']}")
    print(f" * EXIF Metadata Present   : {q_info['has_exif']}")

    if q_info['luma_mean_quant'] > 12.0 or q_info['bits_per_pixel'] < 1.0:
        print(" [!] Multi-Pass Compression Note: High quantization table values confirm aggressive compression (e.g. WhatsApp / messaging re-save).")

    # 2. Document Processing & Segmentation
    detector = DocumentForgeryDetector(tamper_threshold=0.65)
    img_bgr, doc_meta = detector.load_document_image(target_path)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_h, img_w = img_bgr.shape[:2]

    candidate_regions = detector.segment_text_regions(img_bgr)
    ela_map = detector.compute_ela_map(img_bgr, quality=85)
    noise_map = detector.compute_noise_map(gray)

    print("\n--- 2. TEXT REGION SEGMENTATION AUDIT (Over / Under Segmentation) ---")
    print(f" * Total Detected Regions  : {len(candidate_regions)}")
    
    widths = [r["bbox"][2] for r in candidate_regions]
    heights = [r["bbox"][3] for r in candidate_regions]
    areas = [r["area"] for r in candidate_regions]
    
    print(f" * Width Distribution      : Min={min(widths)}px, Max={max(widths)}px, Median={np.median(widths):.1f}px, Mean={np.mean(widths):.1f}px")
    print(f" * Height Distribution     : Min={min(heights)}px, Max={max(heights)}px, Median={np.median(heights):.1f}px, Mean={np.mean(heights):.1f}px")
    print(f" * Total BBox Area Coverage: {sum(areas) / (img_w * img_h) * 100:.2f}% of page surface")

    # Assess segmentation quality for cursive / handwritten vs printed
    stamps = [r for r in candidate_regions if r.get("is_graphic_stamp")]
    lines_or_words = [r for r in candidate_regions if not r.get("is_graphic_stamp")]
    print(f" * Pure Text Fields        : {len(lines_or_words)} regions")
    print(f" * Graphic / Stamp Blocks  : {len(stamps)} regions")

    # 3. Baseline Forensic Statistics
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

    print("\n--- 3. DOCUMENT-WIDE BASELINE METRICS ---")
    print(f" * Baseline Median Stroke Width : {med_stroke:.2f}px (IQR: {iqr_stroke:.2f}px)")
    print(f" * Baseline Median Sharpness    : {med_sharp:.2f} (IQR: {iqr_sharp:.2f})")
    print(f" * Baseline Median ELA Response : {med_ela:.2f} (IQR: {iqr_ela:.2f})")
    print(f" * Baseline Median Paper Noise  : {med_noise:.2f} (IQR: {iqr_noise:.2f})")

    # 4. Per-Region Scores Table (ALL REGIONS)
    print("\n--- 4. PER-REGION TAMPER SCORES & METRICS (ALL REGIONS) ---")
    header = f"{'Region #':<9} | {'BBox (x, y, w, h)':<22} | {'Stroke':<8} | {'Sharpness':<10} | {'ELA':<6} | {'Noise':<6} | {'Tamper Score':<13} | {'Status':<10}"
    print(header)
    print("-" * len(header))

    region_records = []
    for idx, (reg, f) in enumerate(zip(candidate_regions, region_features)):
        bx, by, bw, bh = reg["bbox"]
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

        region_records.append({
            "idx": idx + 1,
            "bbox": reg["bbox"],
            "stroke": f["stroke_width"],
            "sharp": f["edge_sharpness"],
            "ela": f["ela_intensity"],
            "noise": f["noise_variance"],
            "tamper_score": tamper_score,
            "status": status
        })

        print(f"Region #{idx+1:<2} | [{bx:3d}, {by:3d}, {bw:3d}, {bh:3d}]       | {f['stroke_width']:5.2f}px | {f['edge_sharpness']:9.2f} | {f['ela_intensity']:5.2f} | {f['noise_variance']:5.2f} | {tamper_score*100:6.1f}%       | {status:<10}")

    # 5. ELA Signal Statistics vs Clean Baseline
    clean_test_path = "temp_clean_doc.jpg"
    create_genuine_scanned_letter(clean_test_path)
    clean_bgr = cv2.imread(clean_test_path)
    clean_ela = detector.compute_ela_map(clean_bgr, quality=85)
    clean_gray = cv2.cvtColor(clean_bgr, cv2.COLOR_BGR2GRAY)
    clean_noise = detector.compute_noise_map(clean_gray)

    print("\n" + "=" * 95)
    print(" 📊 5. ELA INTENSITY MAP COMPARATIVE STATISTICS")
    print("=" * 95)
    print(f"{'Statistic':<28} | {q_info['file_name']:<32} | {'Clean Scanned Baseline':<28}")
    print("-" * 95)
    print(f"{'ELA Min':<28} | {float(np.min(ela_map)):.2f}                             | {float(np.min(clean_ela)):.2f}")
    print(f"{'ELA Max':<28} | {float(np.max(ela_map)):.2f}                             | {float(np.max(clean_ela)):.2f}")
    print(f"{'ELA Mean':<28} | {float(np.mean(ela_map)):.2f}                             | {float(np.mean(clean_ela)):.2f}")
    print(f"{'ELA Std Dev':<28} | {float(np.std(ela_map)):.2f}                             | {float(np.std(clean_ela)):.2f}")
    print(f"{'ELA 90th Percentile':<28} | {float(np.percentile(ela_map, 90)):.2f}                             | {float(np.percentile(clean_ela, 90)):.2f}")
    print(f"{'Noise Map Mean':<28} | {float(np.mean(noise_map)):.2f}                             | {float(np.mean(clean_noise)):.2f}")
    print(f"{'Noise Map Std Dev':<28} | {float(np.std(noise_map)):.2f}                             | {float(np.std(clean_noise)):.2f}")
    print("=" * 95 + "\n")

    if os.path.exists(clean_test_path):
        os.remove(clean_test_path)


def main():
    # Audit candidates
    candidates = [
        "C:/Users/sheha/Downloads/pp.jpg",
        "C:/Users/sheha/Downloads/po.jpeg",
        "C:/Users/sheha/OneDrive/Desktop/new project/backend/uploads/38e2491d493e_myjpg.jpg"
    ]
    for c in candidates:
        if os.path.exists(c):
            analyze_target_document(c)


if __name__ == "__main__":
    main()
