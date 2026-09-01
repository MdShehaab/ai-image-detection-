"""
Verification script for Image Detector with known Real and AI-Modified samples.
"""

import os
import json
from app import create_app

def run_verification():
    app = create_app("development")
    client = app.test_client()

    samples = [
        ("../test_samples/test/REAL/00000.jpg", "KNOWN REAL (Ground Truth: REAL, Class Index 2)"),
        ("../test_samples/test/AI_MODIFIED/00000.jpg", "KNOWN AI_MODIFIED (Ground Truth: AI_MODIFIED, Class Index 1)"),
        ("../test_samples/test/AI_GENERATED/00000.jpg", "KNOWN AI_GENERATED (Ground Truth: AI_GENERATED, Class Index 0)")
    ]

    print("\n" + "=" * 80)
    print(" [*] VERIFYING IMAGE DETECTION MODEL WITH FIXED PREPROCESSING (RAW 0-255 INPUT)")
    print("=" * 80)

    for img_path, desc in samples:
        if not os.path.exists(img_path):
            print(f"[!] Warning: Sample path {img_path} not found.")
            continue

        print(f"\n--- Testing: {desc} ---")
        with open(img_path, "rb") as f:
            filename = os.path.basename(img_path)
            res = client.post(
                "/api/detect/image",
                data={"file": (f, filename)},
                content_type="multipart/form-data"
            )
            data = json.loads(res.data)
            print(f"Status Code : {res.status_code}")
            print(f"Verdict     : {data.get('verdict')}")
            print(f"Sub-Type    : {data.get('sub_type')}")
            print(f"Confidence  : {data.get('confidence')}%")
            print(f"Probs       : {json.dumps(data.get('probabilities'), indent=2)}")
            print(f"Explanation : {data.get('explanation')}")

    print("\n" + "=" * 80)
    print(" [+] Model Verification Completed.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_verification()
