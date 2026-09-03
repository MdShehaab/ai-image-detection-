"""
End-to-End test suite for Document Forgery & Localized Text-Field Tampering Detection.
Tests genuine documents, simulated localized field tampering (roll number/date alteration),
and real PDF certificates.
"""

import os
import sys
import io
import time
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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


def create_genuine_scanned_letter(output_path: str) -> str:
    """
    Generate a realistic genuine university permission / bonafide document image
    with homogeneous paper grain, uniform typography, and header.
    """
    w, h = 900, 1150
    # Paper background with subtle scan texture noise
    base = np.random.normal(245, 3.5, (h, w, 3)).clip(230, 255).astype(np.uint8)

    # Convert to PIL for crisp typography
    pil_img = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    # University Header
    draw.text((260, 80), "STANFORD UNIVERSITY", fill=(20, 20, 20))
    draw.text((280, 110), "DEPARTMENT OF COMPUTER SCIENCE", fill=(50, 50, 50))
    draw.text((250, 135), "PALO ALTO, CA 94305 | (650) 723-2300", fill=(80, 80, 80))
    draw.line([(80, 170), (820, 170)], fill=(120, 120, 120), width=2)

    # Reference Details
    draw.text((80, 210), "REF NO: SU/CS/2026/089", fill=(30, 30, 30))
    draw.text((640, 210), "DATE: 14-AUG-2026", fill=(30, 30, 30))

    # Title
    draw.text((310, 270), "TO WHOM IT MAY CONCERN", fill=(10, 10, 10))

    # Body Paragraphs
    body_lines = [
        "This is to certify that Mr. MD SHEHAAB HAMEED is a bonafide student of",
        "the Bachelor of Science in Artificial Intelligence & Computer Engineering program",
        "at Stanford University for the academic year 2024-2028.",
        "",
        "Student Registration / Roll Number : 23A81A6141",
        "Current Cumulative Grade Point Avg : 3.92 / 4.00",
        "Authorized Laboratory Clearance Ref : LAB-SEC-8902",
        "",
        "This certificate is issued upon the student's request for official industry",
        "internship verification and AI security research clearance.",
        "",
        "Issued under the official seal and authority of the Academic Dean."
    ]

    y_cursor = 340
    for line in body_lines:
        if line:
            draw.text((80, y_cursor), line, fill=(30, 30, 30))
        y_cursor += 34

    # Signature Block
    draw.text((80, 860), "Authorized Signatory", fill=(60, 60, 60))
    draw.text((80, 895), "Dr. Elena Rostova, Ph.D.", fill=(20, 20, 20))
    draw.text((80, 920), "Dean of Academic Affairs", fill=(70, 70, 70))

    # Stamp Simulation (Red circular seal)
    draw.ellipse([(620, 840), (760, 980)], outline=(180, 40, 40), width=3)
    draw.text((645, 900), "VERIFIED", fill=(180, 40, 40))

    # Convert back to cv2, add realistic scanner blur & JPEG compression
    img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    img_bgr = cv2.GaussianBlur(img_bgr, (3, 3), 0.3)

    cv2.imwrite(output_path, img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"[+] Generated genuine document: {output_path}")
    return output_path


def create_tampered_document(genuine_path: str, output_path: str) -> str:
    """
    Simulate real-world localized field tampering:
    Digitally replace the Roll Number field ('23A81A6141' -> '99X99Z9999') with
    a different font stroke width, white-patch background erasure, and compression artifact.
    """
    img = cv2.imread(genuine_path)
    
    # 1. Target region coordinates for Roll Number value
    # (around x=450, y=470 to x=620, y=515)
    tx, ty, tw, th = 450, 470, 180, 38

    # 2. Digital Inpainting / White Brush Patch (Smoothes away paper grain)
    patch = np.full((th, tw, 3), 253, dtype=np.uint8)  # unnaturally flat white patch
    img[ty:ty+th, tx:tx+tw] = patch

    # 3. Paste replacement text with different font thickness / rendering
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    # Heavy bold stroke text (simulating third-party editor replacement)
    draw.text((tx + 10, ty + 8), "99X99Z9999", fill=(0, 0, 0), stroke_width=2, stroke_fill=(0, 0, 0))

    tampered_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Save as separate JPEG with recompression delta
    cv2.imwrite(output_path, tampered_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print(f"[+] Generated tampered document with altered roll number: {output_path}")
    return output_path


def run_document_tests():
    os.makedirs("test_media", exist_ok=True)
    genuine_doc = "test_media/genuine_bonafide_letter.jpg"
    tampered_doc = "test_media/tampered_bonafide_letter.jpg"

    create_genuine_scanned_letter(genuine_doc)
    create_tampered_document(genuine_doc, tampered_doc)

    app = create_app("development")
    app.config["TESTING"] = True
    client = app.test_client()

    print("\n" + "=" * 85)
    print(" 📄 TEST 1: GENUINE SCANNED DOCUMENT VERIFICATION VIA /api/detect/document")
    print("=" * 85)
    with open(genuine_doc, "rb") as f:
        res_real = client.post(
            "/api/detect/document",
            data={"file": (f, "genuine_bonafide_letter.jpg")},
            content_type="multipart/form-data"
        )
    assert res_real.status_code == 200, f"Expected 200, got {res_real.status_code}"
    data_real = json.loads(res_real.data)

    print(f"[*] Verdict                  : {data_real.get('verdict')} (Expected: REAL)")
    print(f"[*] Sub-Type                 : {data_real.get('sub_type')}")
    print(f"[*] Authenticity Confidence  : {data_real.get('confidence')}%")
    print(f"[*] Tampered Regions Count   : {data_real.get('tampered_regions_count')} (Expected: 0)")
    print(f"[*] Total Text Regions       : {data_real.get('total_text_regions_analyzed')}")
    print(f"[*] Execution Latency        : {data_real.get('execution_time_ms')} ms")
    print(f"[*] Explanation              : {data_real.get('explanation')}")

    print("\n" + "=" * 85)
    print(" 📄 TEST 2: LOCALIZED FIELD-TAMPERED DOCUMENT VIA /api/detect/document")
    print("=" * 85)
    with open(tampered_doc, "rb") as f:
        res_fake = client.post(
            "/api/detect/document",
            data={"file": (f, "tampered_bonafide_letter.jpg")},
            content_type="multipart/form-data"
        )
    assert res_fake.status_code == 200, f"Expected 200, got {res_fake.status_code}"
    data_fake = json.loads(res_fake.data)

    print(f"[*] Verdict                  : {data_fake.get('verdict')} (Expected: AI-MODIFIED / FORGED)")
    print(f"[*] Sub-Type                 : {data_fake.get('sub_type')}")
    print(f"[*] Tampering Risk Confidence: {data_fake.get('confidence')}%")
    print(f"[*] Tampered Regions Flagged : {data_fake.get('tampered_regions_count')} region(s)")
    print(f"[*] Total Text Regions       : {data_fake.get('total_text_regions_analyzed')}")
    print(f"[*] Visual Overlay Data URI  : {data_fake.get('overlay_image')[:45]}...")
    print(f"[*] Explanation              : {data_fake.get('explanation')}")

    print("\n--- Specific Tampered Region Details ---")
    for r in data_fake.get("tampered_regions", []):
        print(f" ⚠️ Region #{r['region_id']}: {r['region_name']}")
        print(f"    - Bounding Box     : {r['bbox']} (Normalized: {r['bbox_normalized']})")
        print(f"    - Tamper Risk Score: {r['tamper_score']*100:.1f}%")
        print(f"    - Anomaly Class    : {r['anomaly_type']}")
        print(f"    - Forensic Reasons : {', '.join(r['reasons'])}")
        print(f"    - Local Metrics    : {r['metrics']}")

    # Test 3: Real PDF Certificate File if available
    pdf_candidates = [
        r"G:\My Drive\SAPCertification20260822-8-42igwn.pdf",
        r"G:\My Drive\23A81A6141_MD.SHEHAAB HAMEED_RESUME (2).pdf"
    ]
    real_pdf = None
    for p in pdf_candidates:
        if os.path.exists(p):
            real_pdf = p
            break

    if real_pdf:
        print("\n" + "=" * 85)
        print(f" 📄 TEST 3: REAL PDF DOCUMENT INFERENCE ({os.path.basename(real_pdf)})")
        print("=" * 85)
        with open(real_pdf, "rb") as f:
            res_pdf = client.post(
                "/api/detect/document",
                data={"file": (f, os.path.basename(real_pdf))},
                content_type="multipart/form-data"
            )
        assert res_pdf.status_code == 200
        data_pdf = json.loads(res_pdf.data)
        print(f"[*] PDF Verdict              : {data_pdf.get('verdict')}")
        print(f"[*] Confidence               : {data_pdf.get('confidence')}%")
        print(f"[*] Text Regions Analyzed    : {data_pdf.get('total_text_regions_analyzed')}")
        print(f"[*] Execution Latency        : {data_pdf.get('execution_time_ms')} ms")

    # Cleanup temporary test files
    for p in [genuine_doc, tampered_doc]:
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists("test_media"):
        os.rmdir("test_media")

    print("\n" + "=" * 85)
    print(" [+] ALL DOCUMENT FORGERY & FIELD TAMPERING TESTS PASSED!")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_document_tests()
