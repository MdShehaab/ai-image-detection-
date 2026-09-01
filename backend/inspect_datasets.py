"""
Read-only dataset inspection script.
Scans dataset directories, produces tree structure, counts files by type,
samples leaf filenames, and reads metadata/label CSV/JSON columns without modifying anything.
"""

import os
import json
import csv
from pathlib import Path
from collections import defaultdict

POTENTIAL_PATHS = [
    Path(r"C:\Users\sheha\OneDrive\Desktop\AI-Powered Visual Deepfake Detection and Analysis System\dataset"),
    Path(r"C:\Users\sheha\OneDrive\Desktop\AI-Powered Visual Deepfake Detection and Analysis System\datasets"),
    Path(r"C:\Users\sheha\OneDrive\Desktop\datasets"),
    Path(r"C:\Users\sheha\OneDrive\Desktop\dataset"),
    Path(r"c:\Users\sheha\OneDrive\Desktop\new project\datasets"),
    Path(r"c:\Users\sheha\OneDrive\Desktop\new project\dataset"),
]

def scan_directory(base_path: Path, max_depth: int = 4):
    if not base_path.exists():
        return None

    report = {
        "root": str(base_path),
        "tree": {},
        "subfolder_stats": {},
        "labels_files": []
    }

    print(f"\n{'='*70}\n[SCANNING DATASET ROOT] {base_path}\n{'='*70}")

    for root, dirs, files in os.walk(base_path):
        rel_path = os.path.relpath(root, base_path)
        depth = len(Path(rel_path).parts) if rel_path != "." else 0
        if depth > max_depth:
            continue

        ext_counts = defaultdict(int)
        for f in files:
            ext = os.path.splitext(f)[1].lower() or "[no_ext]"
            ext_counts[ext] += 1

        sample_files = files[:3]

        report["subfolder_stats"][rel_path] = {
            "depth": depth,
            "total_files": len(files),
            "subdirectories_count": len(dirs),
            "subdirectories": dirs[:10],
            "file_types": dict(ext_counts),
            "sample_files": sample_files
        }

        # Check for label files (csv/json)
        for f in files:
            if f.lower().endswith(('.csv', '.json')):
                file_path = os.path.join(root, f)
                file_size = os.path.getsize(file_path)
                label_info = {
                    "rel_path": os.path.join(rel_path, f),
                    "full_path": file_path,
                    "filename": f,
                    "size_bytes": file_size,
                    "type": "csv" if f.lower().endswith('.csv') else "json",
                    "columns_or_keys": None,
                    "sample_record": None,
                    "total_rows": 0
                }

                try:
                    if f.lower().endswith('.csv'):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
                            reader = csv.reader(csvfile)
                            header = next(reader, None)
                            label_info["columns_or_keys"] = header
                            first_row = next(reader, None)
                            label_info["sample_record"] = first_row
                            # Count total rows
                            count = 1 if header else 0
                            if first_row: count += 1
                            for _ in reader:
                                count += 1
                            label_info["total_rows"] = count
                    elif f.lower().endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as jfile:
                            data = json.load(jfile)
                            if isinstance(data, dict):
                                label_info["columns_or_keys"] = list(data.keys())[:15]
                                label_info["sample_record"] = {k: str(data[k])[:100] for k in list(data.keys())[:3]}
                                label_info["total_rows"] = len(data)
                            elif isinstance(data, list):
                                label_info["total_rows"] = len(data)
                                if len(data) > 0 and isinstance(data[0], dict):
                                    label_info["columns_or_keys"] = list(data[0].keys())
                                    label_info["sample_record"] = data[0]
                except Exception as e:
                    label_info["error"] = str(e)

                report["labels_files"].append(label_info)

    return report

if __name__ == "__main__":
    results = {}
    found_any = False
    for p in POTENTIAL_PATHS:
        if p.exists():
            found_any = True
            rep = scan_directory(p)
            if rep:
                results[str(p)] = rep

    out_file = Path(r"c:\Users\sheha\OneDrive\Desktop\new project\dataset_scan_summary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[DONE] Scan complete. Output written to {out_file}")
