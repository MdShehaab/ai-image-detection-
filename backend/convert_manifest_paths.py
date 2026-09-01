"""
Convert manifest_combined.csv to store dataset-relative paths for Google Colab and Local portability.
Backs up manifest_combined.csv to manifest_combined_absolute_backup.csv before converting.
"""

import shutil
import csv
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\sheha\OneDrive\Desktop\new project").resolve()
MANIFEST_PATH = PROJECT_ROOT / "datasets" / "manifest_combined.csv"
BACKUP_PATH = PROJECT_ROOT / "datasets" / "manifest_combined_absolute_backup.csv"

def convert_path_to_dataset_relative(raw_path: str) -> str:
    """
    Extracts the relative path starting from processed_3class, image_detection, or genimage_extracted.
    Examples:
      - '../.../datasets/processed_3class/train/REAL/00000.jpg' -> 'processed_3class/train/REAL/00000.jpg'
      - '../.../dataset/image_detection/train/ai_generated/000.jpg' -> 'image_detection/train/ai_generated/000.jpg'
      - '../.../datasets/genimage_extracted/imagenet_.../ai/000.png' -> 'genimage_extracted/imagenet_.../ai/000.png'
    """
    p = raw_path.replace("\\", "/").strip()
    
    # Target dataset folder prefixes
    for root_name in ["processed_3class/", "image_detection/", "genimage_extracted/"]:
        if root_name in p:
            idx = p.find(root_name)
            return p[idx:]
            
    # Also check 'dataset/image_detection/'
    if "dataset/image_detection/" in p:
        idx = p.find("dataset/image_detection/")
        return p[idx + len("dataset/"):]

    return p

def run_conversion():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
        
    print(f"[*] Creating backup at {BACKUP_PATH}...")
    shutil.copy2(MANIFEST_PATH, BACKUP_PATH)
    print(f"[*] Backup successfully created ({BACKUP_PATH.stat().st_size / (1024*1024):.2f} MB).")
    
    converted_rows = []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            row["image_path"] = convert_path_to_dataset_relative(row["image_path"])
            converted_rows.append(row)
            
    print(f"[*] Writing converted manifest with {len(converted_rows):,} rows...")
    with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(converted_rows)
        
    print(f"[PASS] Successfully updated {MANIFEST_PATH} in place.")
    print("\nSample converted paths:")
    for r in converted_rows[:5]:
        print("  -", r["image_path"])

if __name__ == "__main__":
    run_conversion()
