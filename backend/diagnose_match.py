"""
diagnose_match.py
=================
Prints ORB inliers, phash distance, and diff metrics between
a query image and every registered original in the registry.

Usage:
    python diagnose_match.py <path_to_query_image>

Example:
    python diagnose_match.py "C:/Users/me/Desktop/gemini_edit.jpg"
"""
import sys
import os
import cv2
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, str(Path(__file__).parent))

import registry.store as rs

def diagnose(query_path: str, registry_base: str = None):
    if registry_base is None:
        registry_base = str(Path(__file__).parent / "registry" / "data")

    print("=" * 72)
    print(f"  REFERENCE CHECK DIAGNOSTICS")
    print(f"  Query: {query_path}")
    print("=" * 72)

    if not os.path.exists(query_path):
        print(f"ERROR: File not found: {query_path}")
        sys.exit(1)

    # Load and resize query
    try:
        query_bgr = rs._load_bgr(query_path)
    except Exception as e:
        print(f"ERROR loading image: {e}")
        sys.exit(1)

    query_rs   = rs._resize_longest(query_bgr, rs.THUMB_SIZE)
    query_gray = cv2.cvtColor(query_rs, cv2.COLOR_BGR2GRAY)
    query_ph   = rs._phash_from_bgr(query_rs)

    print(f"\nQuery image:  {query_bgr.shape[1]}x{query_bgr.shape[0]}px")
    print(f"Resized to:   {query_rs.shape[1]}x{query_rs.shape[0]}px")
    print(f"phash:        {query_ph}")
    print()

    originals = rs.list_originals(registry_base)
    if not originals:
        print("Registry is empty. Register at least one original first.")
        sys.exit(0)

    print(f"Registry entries: {len(originals)}")
    print()

    header = (f"{'ID':>10}  {'Filename':<30}  {'ORB inliers':>11}  "
              f"{'phash dist':>10}  {'cand?':>6}  {'chg%':>7}  {'lgr%':>7}  verdict")
    print(header)
    print("-" * len(header))

    for entry in originals:
        eid   = entry.get("id", "?")[:8]
        fname = entry.get("filename", "?")[:30]
        tp    = entry.get("thumb_path", "")

        if not tp or not os.path.exists(tp):
            print(f"  {eid}  {fname:<30}  [MISSING THUMBNAIL]")
            continue

        try:
            ref_bgr  = rs._load_bgr(tp)
            ref_gray = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            print(f"  {eid}  {fname:<30}  ERROR loading ref: {e}")
            continue

        ph_dist   = rs._hamming(query_ph, entry.get("phash"))
        inliers, H = rs._best_orb(query_gray, ref_gray, rs.ORB_INLIER_THRESHOLD)

        is_cand = (inliers >= rs.ORB_INLIER_THRESHOLD) and (ph_dist <= rs.PHASH_THRESHOLD)

        try:
            diff = rs._analyse_diff(query_rs, ref_bgr, H)
            chg  = diff["changed_area_pct"]
            lgr  = diff["largest_region_pct"]
            chg_s = f"{chg:.3f}%"
            lgr_s = f"{lgr:.3f}%"
            verdict = "REAL" if chg < rs.MODIFIED_AREA_THRESHOLD and lgr < rs.MODIFIED_REGION_THRESHOLD else "AI-MODIFIED"
        except Exception as e:
            chg_s = lgr_s = "ERR"
            verdict = f"diff-err: {e}"

        cand_s = "YES" if is_cand else "no"
        print(f"  {eid}  {fname:<30}  {inliers:>11}  {ph_dist:>10}  {cand_s:>6}  "
              f"{chg_s:>7}  {lgr_s:>7}  {verdict if is_cand else '—'}")

    print()
    print("Thresholds:")
    print(f"  ORB inlier threshold   : {rs.ORB_INLIER_THRESHOLD}  (both ORB AND phash must qualify)")
    print(f"  phash Hamming threshold: {rs.PHASH_THRESHOLD}")
    print(f"  diff amplitude cutoff  : {rs.DIFF_AMPLITUDE_CUTOFF}")
    print(f"  MODIFIED area threshold: {rs.MODIFIED_AREA_THRESHOLD}%")
    print(f"  MODIFIED region thresh : {rs.MODIFIED_REGION_THRESHOLD}%")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    diagnose(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
