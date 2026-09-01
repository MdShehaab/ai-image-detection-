"""
Build unified manifest for Image Detection Module.
Combines processed_3class, image_detection, and genimage_extracted datasets into datasets/manifest_combined.csv.
"""

import os
import csv
from pathlib import Path
from collections import defaultdict, Counter

PROJECT_ROOT = Path(r"c:\Users\sheha\OneDrive\Desktop\new project").resolve()
OUTPUT_DIR = PROJECT_ROOT / "datasets"
OUTPUT_MANIFEST = OUTPUT_DIR / "manifest_combined.csv"
OUTPUT_MISSING = OUTPUT_DIR / "manifest_missing.csv"

DATASET_PARENT = Path(r"C:\Users\sheha\OneDrive\Desktop\AI-Powered Visual Deepfake Detection and Analysis System").resolve()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

def normalize_class(class_name: str) -> str:
    c = str(class_name).strip().lower()
    if c in ("ai_generated", "aigenerated", "fake", "synthetic"):
        return "ai_generated"
    elif c in ("ai_modified", "aimodified", "modified", "manipulated"):
        return "ai_modified"
    elif c in ("real", "genuine", "nature", "authentic"):
        return "real"
    return c

def to_project_rel_path(abs_path: Path) -> str:
    """Convert absolute Path to forward-slashed path relative to PROJECT_ROOT."""
    rel = os.path.relpath(abs_path, PROJECT_ROOT)
    return rel.replace("\\", "/")

def build_manifest():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    valid_records = []
    missing_records = []
    
    print("[1/3] Processing processed_3class/ metadata.csv...")
    meta_path = DATASET_PARENT / "datasets" / "processed_3class" / "metadata.csv"
    if not meta_path.exists():
        print(f"[WARN] metadata.csv not found at {meta_path}")
    else:
        with open(meta_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_rel = row.get("image_path", "").strip()
                norm_class = normalize_class(row.get("class", ""))
                src_dataset = row.get("source_dataset", "processed_3class").strip()
                src_category = row.get("source_category", "").strip()
                split = row.get("split", "train").strip().lower()
                
                # Resolve absolute path
                abs_file = (DATASET_PARENT / raw_rel).resolve()
                if abs_file.exists():
                    valid_records.append({
                        "image_path": to_project_rel_path(abs_file),
                        "class": norm_class,
                        "source_dataset": f"processed_3class ({src_dataset})" if src_dataset else "processed_3class",
                        "source_category": src_category or norm_class,
                        "split": split
                    })
                else:
                    missing_records.append({
                        "attempted_path": str(abs_file),
                        "dataset": "processed_3class",
                        "error_reason": "File not found on disk"
                    })
                    
    print(f"      -> processed_3class valid: {len(valid_records)}, missing: {len(missing_records)}")

    print("[2/3] Processing image_detection/ directory...")
    img_det_dir = DATASET_PARENT / "dataset" / "image_detection"
    if not img_det_dir.exists():
        print(f"[WARN] image_detection directory not found at {img_det_dir}")
    else:
        for split in ("train", "validation", "test"):
            split_dir = img_det_dir / split
            if not split_dir.exists():
                continue
            for class_dir_name in ("ai_generated", "ai_modified", "real"):
                c_dir = split_dir / class_dir_name
                if not c_dir.exists():
                    continue
                norm_class = normalize_class(class_dir_name)
                for root, _, files in os.walk(c_dir):
                    for fname in files:
                        if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                            abs_file = (Path(root) / fname).resolve()
                            if abs_file.exists():
                                valid_records.append({
                                    "image_path": to_project_rel_path(abs_file),
                                    "class": norm_class,
                                    "source_dataset": "image_detection",
                                    "source_category": norm_class,
                                    "split": split
                                })
                            else:
                                missing_records.append({
                                    "attempted_path": str(abs_file),
                                    "dataset": "image_detection",
                                    "error_reason": "File not found on disk"
                                })

    print(f"      -> Cumulative valid: {len(valid_records)}, missing: {len(missing_records)}")

    print("[3/3] Processing genimage_extracted/ directory...")
    genimage_dir = DATASET_PARENT / "datasets" / "genimage_extracted"
    if not genimage_dir.exists():
        print(f"[WARN] genimage_extracted not found at {genimage_dir}")
    else:
        for root, _, files in os.walk(genimage_dir):
            if not files:
                continue
            root_path = Path(root)
            parts_lower = [p.lower() for p in root_path.parts]
            
            # Determine class
            norm_class = None
            if "ai" in parts_lower:
                norm_class = "ai_generated"
            elif "nature" in parts_lower:
                norm_class = "real"
            
            if not norm_class:
                continue
                
            # Extract generator name
            gen_name = "genimage"
            for p in root_path.parts:
                pl = p.lower()
                if "midjourney" in pl:
                    gen_name = "midjourney"
                    break
                elif "wukong" in pl:
                    gen_name = "wukong"
                    break
                elif "sdv5" in pl or "sd" in pl:
                    gen_name = "sdv5"
                    break
                elif "glide" in pl:
                    gen_name = "glide"
                    break

            category = f"{gen_name}_{norm_class}" if norm_class == "ai_generated" else f"imagenet_{gen_name}_nature"

            for fname in files:
                if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                    abs_file = (root_path / fname).resolve()
                    if abs_file.exists():
                        valid_records.append({
                            "image_path": to_project_rel_path(abs_file),
                            "class": norm_class,
                            "source_dataset": f"genimage_{gen_name}",
                            "source_category": category,
                            "split": "train" # Default split per instructions
                        })
                    else:
                        missing_records.append({
                            "attempted_path": str(abs_file),
                            "dataset": f"genimage_{gen_name}",
                            "error_reason": "File not found on disk"
                        })

    print(f"\n[DONE] Finished scanning. Writing manifests...")
    
    # Write manifest_combined.csv
    fieldnames = ["image_path", "class", "source_dataset", "source_category", "split"]
    with open(OUTPUT_MANIFEST, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_records)

    # Write manifest_missing.csv
    with open(OUTPUT_MISSING, mode="w", newline="", encoding="utf-8") as f:
        missing_fields = ["attempted_path", "dataset", "error_reason"]
        writer = csv.DictWriter(f, fieldnames=missing_fields)
        writer.writeheader()
        writer.writerows(missing_records)

    print(f"[*] Manifest saved to: {OUTPUT_MANIFEST}")
    print(f"[*] Missing log saved to: {OUTPUT_MISSING}")

    # Generate Balance & Summary Statistics
    generate_summary_report(valid_records, missing_records)

def generate_summary_report(records, missing_records):
    total = len(records)
    print("\n" + "="*80)
    print(f"               UNIFIED IMAGE DATASET MANIFEST SUMMARY")
    print("="*80)
    print(f"Total Valid Images Indexed : {total:,}")
    print(f"Total Missing Files Logged : {len(missing_records):,}")
    print("-"*80)

    # Breakdown by Split & Class
    split_class_counts = defaultdict(Counter)
    dataset_class_counts = defaultdict(Counter)
    class_totals = Counter()
    split_totals = Counter()
    dataset_totals = Counter()

    for r in records:
        s = r["split"]
        c = r["class"]
        d = r["source_dataset"]
        split_class_counts[s][c] += 1
        dataset_class_counts[d][c] += 1
        class_totals[c] += 1
        split_totals[s] += 1
        dataset_totals[d] += 1

    classes = sorted(list(class_totals.keys()))

    # Table 1: Split x Class
    print("\n[TABLE 1: Breakdown by Split & Class]")
    header = f"{'Split':<15}" + "".join([f"{c:<16}" for c in classes]) + f"{'Total':<12}"
    print(header)
    print("-" * len(header))
    for s in ("train", "validation", "test"):
        if s in split_totals:
            row_str = f"{s:<15}"
            for c in classes:
                cnt = split_class_counts[s][c]
                pct = (cnt / split_totals[s] * 100) if split_totals[s] > 0 else 0
                row_str += f"{cnt:,} ({pct:.1f}%)".ljust(16)
            row_str += f"{split_totals[s]:,}".ljust(12)
            print(row_str)
    
    print("-" * len(header))
    tot_row = f"{'TOTAL':<15}"
    for c in classes:
        cnt = class_totals[c]
        pct = (cnt / total * 100) if total > 0 else 0
        tot_row += f"{cnt:,} ({pct:.1f}%)".ljust(16)
    tot_row += f"{total:,}".ljust(12)
    print(tot_row)

    # Table 2: Source Dataset x Class
    print("\n[TABLE 2: Breakdown by Source Dataset & Class]")
    header2 = f"{'Source Dataset':<35}" + "".join([f"{c:<16}" for c in classes]) + f"{'Total':<12}"
    print(header2)
    print("-" * len(header2))
    for d, d_cnt in sorted(dataset_totals.items(), key=lambda x: -x[1]):
        row_str = f"{d:<35}"
        for c in classes:
            cnt = dataset_class_counts[d][c]
            row_str += f"{cnt:,}".ljust(16)
        row_str += f"{d_cnt:,}".ljust(12)
        print(row_str)
    print("-" * len(header2))

    # Balance Assessment & Imbalance Flagging
    print("\n[TABLE 3: Class Imbalance & Weighting Analysis]")
    min_class_name, min_count = min(class_totals.items(), key=lambda x: x[1])
    max_class_name, max_count = max(class_totals.items(), key=lambda x: x[1])
    overall_ratio = max_count / max(1, min_count)

    print(f" - Min Class : '{min_class_name}' ({min_count:,} samples, {min_count/total*100:.1f}%)")
    print(f" - Max Class : '{max_class_name}' ({max_count:,} samples, {max_count/total*100:.1f}%)")
    print(f" - Max / Min Ratio : {overall_ratio:.2f}x")

    if overall_ratio > 2.0:
        print(f" [!] FLAG: SEVERE CLASS IMBALANCE DETECTED (> 2.0x).")
        print(f"     Class '{max_class_name}' has {overall_ratio:.2f}x more samples than '{min_class_name}'.")
        print(f"     -> Recommendation: Apply class weights in loss function or perform under/oversampling.")
    else:
        print(f" [OK] Classes are reasonably balanced overall (Ratio <= 2.0x).")

    # Check per-split balance
    print("\n Per-Split Imbalance Details:")
    for s in ("train", "validation", "test"):
        counts = [split_class_counts[s][c] for c in classes if split_class_counts[s][c] > 0]
        if counts:
            s_ratio = max(counts) / min(counts)
            flag = "[!] IMBALANCED (>2x)" if s_ratio > 2.0 else "[OK] Balanced"
            print(f"   * Split '{s}': Max/Min Ratio = {s_ratio:.2f}x -> {flag}")

    print("="*80 + "\n")

if __name__ == "__main__":
    build_manifest()
