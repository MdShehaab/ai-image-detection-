"""
registry/store.py  –  v3
========================
Manages on-disk registry of "trusted original" images and the reference-check
matching pipeline.  Two independent matching paths run in parallel:

  PATH A – ORB + phash
    Works when the scene / background is mostly unchanged.
    Fails on whole-scene AI re-renders.

  PATH B – Face embedding (MTCNN + pixel descriptor or ArcFace ONNX)
    Works when the same face is present regardless of background.
    Four-gate check: cosine similarity, box-centre shift, size ratio, landmark RMSE.

Verdict resolver (in priority order):
  1. ORB matched  AND  small change  →  REAL  ("Registered original")
  2. ORB matched  AND  large change  →  AI-MODIFIED  (diff boxes shown)
  3. Face matched (no ORB)           →  AI-MODIFIED  (scene differs; no diff boxes;
                                         show registered thumbnail instead)
  4. No match                        →  CNN verdict

Storage layout:
  <registry_base>/<id>/
      original.jpg   – 512-px longest-side thumbnail (RGB JPEG, q95)
      meta.json      – {id, filename, phash, face_meta, registered_at, thumb_path}
"""

import os
import uuid
import json
import time
import logging
import shutil
import numpy as np
import cv2
from pathlib import Path
from PIL import Image

try:
    import imagehash
    _IMAGEHASH_AVAILABLE = True
except ImportError:
    _IMAGEHASH_AVAILABLE = False
    logging.warning("[Registry] imagehash not installed – phash disabled.")

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Tuneable thresholds – overridden from Flask config in routes.py
# ─────────────────────────────────────────────────────────────────────────────
ORB_INLIER_THRESHOLD      = 15    # min RANSAC inliers for ORB candidate
PHASH_THRESHOLD           = 20    # max phash Hamming distance for ORB candidate
DIFF_AMPLITUDE_CUTOFF     = 25    # suppress pixel diffs below this (JPEG noise)
MODIFIED_AREA_THRESHOLD   = 0.4   # changed_area_pct >= this → MODIFIED
MODIFIED_REGION_THRESHOLD = 0.15  # single-region_pct >= this → MODIFIED
THUMB_SIZE                = 512   # longest side of stored thumbnail

# Face matcher thresholds
FACE_SIM_ARCFACE    = 0.60   # cosine similarity (ArcFace ONNX)
FACE_SIM_PIXEL      = 0.88   # cosine similarity (pixel fallback – higher bar)
FACE_BOX_CENTER_SHIFT = 0.12  # max face-box centre drift (fraction of W/H)
FACE_SIZE_RATIO_MIN   = 0.75  # min(upload/ref) face-box area ratio
FACE_SIZE_RATIO_MAX   = 1.33  # max(upload/ref) face-box area ratio
FACE_LANDMARK_RMSE    = 0.06  # max landmark RMSE (normalised coords)


# ─────────────────────────────────────────────────────────────────────────────
# Image I/O helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_bgr(path: str) -> np.ndarray:
    """
    Robust image loader: handles JPEG, PNG, RGBA, palette, 16-bit, WEBP.
    Always returns a 3-channel uint8 BGR array.
    Raises ValueError on failure.
    """
    # Try cv2 first (fast path)
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is not None:
        if img.ndim == 2:                         # grayscale
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:                   # BGRA
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif img.shape[2] == 3:
            pass                                  # already BGR
        if img.dtype != np.uint8:
            img = (img / 256).astype(np.uint8) if img.max() > 255 else img.astype(np.uint8)
        return img

    # Fallback: PIL handles palette / exotic formats
    try:
        pil = Image.open(path)
        pil = pil.convert("RGB")
        arr = np.array(pil, dtype=np.uint8)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise ValueError(f"Cannot read image at {path}: {e}")


def _resize_longest(img: np.ndarray, longest: int = THUMB_SIZE) -> np.ndarray:
    """Resize so the longest side == `longest`, preserving aspect ratio."""
    h, w = img.shape[:2]
    if max(h, w) <= longest:
        return img
    scale = longest / max(h, w)
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


# ─────────────────────────────────────────────────────────────────────────────
# Perceptual hash
# ─────────────────────────────────────────────────────────────────────────────

def _phash_from_path(path: str) -> str | None:
    if not _IMAGEHASH_AVAILABLE:
        return None
    try:
        pil = Image.open(path).convert("RGB")
        return str(imagehash.phash(pil))
    except Exception as e:
        logger.debug(f"[Registry] phash({path}): {e}")
        return None


def _phash_from_bgr(img: np.ndarray) -> str | None:
    if not _IMAGEHASH_AVAILABLE:
        return None
    try:
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return str(imagehash.phash(pil))
    except Exception as e:
        logger.debug(f"[Registry] phash(array): {e}")
        return None


def _hamming(h1: str | None, h2: str | None) -> int:
    if not _IMAGEHASH_AVAILABLE or h1 is None or h2 is None:
        return 9999
    try:
        return imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)
    except Exception:
        return 9999


# ─────────────────────────────────────────────────────────────────────────────
# ORB matching
# ─────────────────────────────────────────────────────────────────────────────

_orb = cv2.ORB_create(nfeatures=2000)


def _orb_match(query_gray: np.ndarray, ref_gray: np.ndarray,
               threshold: int) -> tuple[int, np.ndarray | None]:
    """
    ORB + Lowe ratio test + RANSAC homography.
    Returns (inlier_count, H_matrix | None).
    H is always returned when inliers >= threshold (even partial match).
    """
    kp1, d1 = _orb.detectAndCompute(query_gray, None)
    kp2, d2 = _orb.detectAndCompute(ref_gray,   None)
    if d1 is None or d2 is None or len(kp1) < 4 or len(kp2) < 4:
        return 0, None

    bf   = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    raw  = bf.knnMatch(d1, d2, k=2)
    good = [m for pair in raw if len(pair) == 2
            for m, n in [pair] if m.distance < 0.75 * n.distance]

    if len(good) < 4:
        return len(good), None

    pts1 = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5.0)
    if mask is None:
        return 0, None

    inliers = int(mask.sum())
    return inliers, (H if inliers >= threshold else None)


def _centre_crop(img: np.ndarray, frac: float = 0.6) -> np.ndarray:
    """Return centre `frac` × `frac` crop of the image."""
    h, w = img.shape[:2]
    dy = int(h * (1 - frac) / 2)
    dx = int(w * (1 - frac) / 2)
    return img[dy: h - dy, dx: w - dx]


def _best_orb(query_gray: np.ndarray, ref_gray: np.ndarray,
              threshold: int) -> tuple[int, np.ndarray | None]:
    """
    Try ORB on full image, then on centre crop if full fails.
    Returns best (inliers, H).
    """
    inliers_full, H_full = _orb_match(query_gray, ref_gray, threshold)
    if inliers_full >= threshold:
        return inliers_full, H_full

    # Centre crop (handles background replacement scenarios)
    q_crop = _centre_crop(query_gray)
    r_crop = _centre_crop(ref_gray)
    inliers_crop, _ = _orb_match(q_crop, r_crop, threshold)

    if inliers_crop > inliers_full:
        # Use full H even if only crop matched (we need to warp full image)
        return inliers_crop, H_full
    return inliers_full, H_full


# ─────────────────────────────────────────────────────────────────────────────
# Difference analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyse_diff(query_bgr: np.ndarray, ref_bgr: np.ndarray,
                  H: np.ndarray | None) -> dict:
    """
    Align query → reference frame, compute blurred absolute difference,
    suppress JPEG/resize noise, morphological-clean, extract connected regions.

    Returns:
        changed_area_pct      – float
        largest_region_pct    – float  (largest single CC as % of image)
        regions               – list[{x,y,width,height,area_px,region_pct}]  (normalised 0-1)
    """
    h_ref, w_ref = ref_bgr.shape[:2]

    # ── Alignment ──────────────────────────────────────────────────────────
    if H is not None:
        try:
            aligned = cv2.warpPerspective(
                query_bgr, H, (w_ref, h_ref),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
        except Exception:
            aligned = cv2.resize(query_bgr, (w_ref, h_ref))
    else:
        # Scale query to exactly fit ref (handles crops / aspect-ratio edits)
        aligned = cv2.resize(query_bgr, (w_ref, h_ref), interpolation=cv2.INTER_LINEAR)

    # Ensure both are uint8 3-channel
    aligned = np.clip(aligned, 0, 255).astype(np.uint8)
    ref_u8  = np.clip(ref_bgr, 0, 255).astype(np.uint8)

    # ── Blur to suppress JPEG block artefacts ──────────────────────────────
    blur_k  = 5
    ref_b   = cv2.GaussianBlur(ref_u8,  (blur_k, blur_k), 0)
    aln_b   = cv2.GaussianBlur(aligned, (blur_k, blur_k), 0)

    # ── Per-pixel max-channel absolute difference ──────────────────────────
    diff    = cv2.absdiff(ref_b, aln_b)         # uint8, no overflow
    diff_1c = diff.max(axis=2).astype(np.uint8)  # (H, W)

    # ── Threshold: suppress low-amplitude JPEG / resize noise ─────────────
    _, mask = cv2.threshold(diff_1c, int(DIFF_AMPLITUDE_CUTOFF), 255, cv2.THRESH_BINARY)
    mask    = mask.astype(np.uint8)

    # ── Morphological clean-up ─────────────────────────────────────────────
    k    = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)

    # ── Metrics ───────────────────────────────────────────────────────────
    total_px          = h_ref * w_ref
    changed_px        = int(np.count_nonzero(mask))
    changed_area_pct  = round(changed_px / total_px * 100, 4)

    # ── Connected components → bounding boxes ─────────────────────────────
    regions: list[dict] = []
    largest_region_pct  = 0.0

    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    # stats[i]: [LEFT, TOP, WIDTH, HEIGHT, AREA];  label 0 = background
    cc = sorted(
        [(stats[i, cv2.CC_STAT_AREA], i) for i in range(1, n)],
        reverse=True,
    )
    for area, idx in cc[:5]:
        if area < 150:
            continue
        x = int(stats[idx, cv2.CC_STAT_LEFT])
        y = int(stats[idx, cv2.CC_STAT_TOP])
        w = int(stats[idx, cv2.CC_STAT_WIDTH])
        h = int(stats[idx, cv2.CC_STAT_HEIGHT])
        rp = round(area / total_px * 100, 4)
        largest_region_pct = max(largest_region_pct, rp)
        regions.append({
            "x":          round(x / w_ref, 4),
            "y":          round(y / h_ref, 4),
            "width":      round(w / w_ref, 4),
            "height":     round(h / h_ref, 4),
            "area_px":    int(area),
            "region_pct": rp,
        })

    return {
        "changed_area_pct":   changed_area_pct,
        "largest_region_pct": round(largest_region_pct, 4),
        "regions":            regions,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public Registry API
# ─────────────────────────────────────────────────────────────────────────────

def _registry_dir(base: str) -> Path:
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def register_original(image_path: str, original_filename: str,
                       registry_base: str) -> dict:
    """
    Store a new registered original.  Returns the entry metadata dict.
    Converts any image format (RGBA, palette, 16-bit…) to RGB JPEG.
    Also detects and stores the largest face embedding + landmarks.
    """
    entry_id  = str(uuid.uuid4())
    entry_dir = _registry_dir(registry_base) / entry_id
    entry_dir.mkdir(parents=True, exist_ok=True)

    img        = _load_bgr(image_path)
    thumb      = _resize_longest(img, THUMB_SIZE)
    thumb_path = str(entry_dir / "original.jpg")
    cv2.imwrite(thumb_path, thumb, [cv2.IMWRITE_JPEG_QUALITY, 95])

    phash_val = _phash_from_path(thumb_path)

    # ── Face embedding (best-effort; None if no face / deps missing) ──────
    face_meta = None
    try:
        from registry.face_embed import get_face_meta as _gfm
        face_meta = _gfm(thumb)
        if face_meta:
            # Drop the full pixel embedding from meta for storage efficiency
            # (keep it as a key but store it – it's ~4096 floats ≈ 32 KB)
            logger.info(f"[Registry] Face detected for {entry_id} "
                        f"(score={face_meta['score']:.2f}, "
                        f"mode={face_meta['mode']})")
    except Exception as e:
        logger.warning(f"[Registry] Face meta failed: {e}")

    meta = {
        "id":            entry_id,
        "filename":      original_filename,
        "phash":         phash_val,
        "face_meta":     face_meta,
        "registered_at": time.time(),
        "thumb_path":    thumb_path,
    }
    (entry_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    logger.info(f"[Registry] Registered {entry_id} ({original_filename})")
    return meta


def list_originals(registry_base: str) -> list[dict]:
    """Return all registered originals, newest first."""
    base   = _registry_dir(registry_base)
    result = []
    for entry_dir in base.iterdir():
        mp = entry_dir / "meta.json"
        if mp.exists():
            try:
                result.append(json.loads(mp.read_text()))
            except Exception as e:
                logger.warning(f"[Registry] Bad meta at {mp}: {e}")
    result.sort(key=lambda m: m.get("registered_at", 0), reverse=True)
    return result


def delete_original(entry_id: str, registry_base: str) -> bool:
    """Permanently remove a registered original. Returns True on success."""
    entry_dir = _registry_dir(registry_base) / entry_id
    if not entry_dir.exists():
        return False
    shutil.rmtree(str(entry_dir))
    logger.info(f"[Registry] Deleted {entry_id}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Face-matching helpers
# ─────────────────────────────────────────────────────────────────────────────

def _face_candidate(
    query_face: dict | None,
    reg_face:   dict | None,
    sim_thresh:   float = FACE_SIM_PIXEL,
    shift_thresh: float = FACE_BOX_CENTER_SHIFT,
    ratio_min:    float = FACE_SIZE_RATIO_MIN,
    ratio_max:    float = FACE_SIZE_RATIO_MAX,
    lm_thresh:    float = FACE_LANDMARK_RMSE,
) -> tuple[bool, dict]:
    """
    Returns (is_candidate, debug_dict).
    ALL four gates must pass.
    """
    dbg = {"face_sim": None, "box_shift": None, "size_ratio": None,
           "lm_rmse": None, "gate_failed": None}

    if not query_face or not reg_face:
        dbg["gate_failed"] = "no_face"
        return False, dbg

    from registry.face_embed import cosine_sim as _csim, landmark_rmse as _lrmse

    # Gate 1 – embedding similarity
    sim = _csim(query_face["embedding"], reg_face["embedding"])
    dbg["face_sim"] = round(sim, 4)
    if sim < sim_thresh:
        dbg["gate_failed"] = "similarity"
        return False, dbg

    # Gate 2 – face-box centre shift
    qb = query_face["box_norm"]; rb = reg_face["box_norm"]
    qcx = qb[0] + qb[2] / 2;  qcy = qb[1] + qb[3] / 2
    rcx = rb[0] + rb[2] / 2;  rcy = rb[1] + rb[3] / 2
    shift = ((qcx - rcx) ** 2 + (qcy - rcy) ** 2) ** 0.5
    dbg["box_shift"] = round(shift, 4)
    if shift > shift_thresh:
        dbg["gate_failed"] = "box_shift"
        return False, dbg

    # Gate 3 – face-box size ratio
    q_area = qb[2] * qb[3]
    r_area = rb[2] * rb[3]
    ratio  = (q_area / r_area) if r_area > 1e-9 else 999
    dbg["size_ratio"] = round(ratio, 4)
    if not (ratio_min <= ratio <= ratio_max):
        dbg["gate_failed"] = "size_ratio"
        return False, dbg

    # Gate 4 – landmark RMSE
    lm_rmse = _lrmse(query_face["landmarks_norm"], reg_face["landmarks_norm"])
    dbg["lm_rmse"] = round(lm_rmse, 4)
    if lm_rmse > lm_thresh:
        dbg["gate_failed"] = "landmarks"
        return False, dbg

    dbg["gate_failed"] = None
    return True, dbg


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_reference_check(
    upload_path:       str,
    registry_base:     str,
    orb_threshold:     int   = ORB_INLIER_THRESHOLD,
    phash_threshold:   int   = PHASH_THRESHOLD,
    modified_area:     float = MODIFIED_AREA_THRESHOLD,
    modified_region:   float = MODIFIED_REGION_THRESHOLD,
    face_sim_arcface:  float = FACE_SIM_ARCFACE,
    face_sim_pixel:    float = FACE_SIM_PIXEL,
    face_box_shift:    float = FACE_BOX_CENTER_SHIFT,
    face_ratio_min:    float = FACE_SIZE_RATIO_MIN,
    face_ratio_max:    float = FACE_SIZE_RATIO_MAX,
    face_lm_rmse:      float = FACE_LANDMARK_RMSE,
) -> dict:

    """
    Compare upload against all registered originals (two paths: ORB + face).

    Returns dict keys: matched, match_method, original_id, original_filename,
    thumb_path, verdict, sub_label, changed_area_pct, largest_region_pct,
    regions, debug.
    match_method: "orb" | "face" | None
    """
    no_match: dict = {
        "matched":            False,
        "match_method":       None,
        "original_id":        None,
        "original_filename":  None,
        "thumb_path":         None,
        "verdict":            None,
        "sub_label":          None,
        "changed_area_pct":   None,
        "largest_region_pct": None,
        "regions":            [],
        "debug":              {},
    }

    originals = list_originals(registry_base)
    if not originals:
        return no_match

    try:
        query_bgr = _load_bgr(upload_path)
    except ValueError as e:
        logger.warning(f"[Registry] {e}")
        return no_match

    query_rs   = _resize_longest(query_bgr, THUMB_SIZE)
    query_gray = cv2.cvtColor(query_rs, cv2.COLOR_BGR2GRAY)
    query_ph   = _phash_from_bgr(query_rs)

    # Face embedding for query
    query_face = None
    face_sim_thresh = face_sim_pixel
    try:
        from registry.face_embed import get_face_meta as _gfm, EMBED_MODE
        query_face = _gfm(query_rs)
        face_sim_thresh = (face_sim_arcface if EMBED_MODE == "arcface"
                           else face_sim_pixel)
    except Exception as e:
        logger.debug(f"[Registry] face embed query: {e}")

    # Score every original on both paths
    orb_best_score   = -1e9
    orb_best_entry   = None
    orb_best_inliers = 0
    orb_best_ph_dist = 9999
    orb_best_H       = None
    face_best_score  = -1e9
    face_best_entry  = None
    face_best_dbg: dict = {}

    for entry in originals:
        thumb_path = entry.get("thumb_path", "")
        if not thumb_path or not os.path.exists(thumb_path):
            continue

        # ORB path
        try:
            ref_bgr  = _load_bgr(thumb_path)
            ref_gray = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2GRAY)
        except Exception:
            continue
        ph_dist    = _hamming(query_ph, entry.get("phash"))
        inliers, H = _best_orb(query_gray, ref_gray, orb_threshold)
        if (inliers >= orb_threshold) and (ph_dist <= phash_threshold):
            score = inliers * 10 - ph_dist
            if score > orb_best_score:
                orb_best_score   = score
                orb_best_entry   = entry
                orb_best_inliers = inliers
                orb_best_ph_dist = ph_dist
                orb_best_H       = H

        # Face path
        reg_face = entry.get("face_meta")
        is_face_cand, fdbg = _face_candidate(
            query_face, reg_face,
            sim_thresh=face_sim_thresh,
            shift_thresh=face_box_shift,
            ratio_min=face_ratio_min,
            ratio_max=face_ratio_max,
            lm_thresh=face_lm_rmse,
        )
        if is_face_cand:
            score = fdbg.get("face_sim") or 0.0
            if score > face_best_score:
                face_best_score = score
                face_best_entry = entry
                face_best_dbg   = fdbg

    # RULE 1 & 2: ORB match (higher priority)
    if orb_best_entry is not None:
        try:
            ref_bgr = _load_bgr(orb_best_entry["thumb_path"])
            ref_rs  = _resize_longest(ref_bgr, THUMB_SIZE)
            diff    = _analyse_diff(query_rs, ref_rs, orb_best_H)
        except Exception as e:
            logger.exception(f"[Registry] _analyse_diff failed: {e}")
            return {
                **no_match,
                "matched":           True,
                "match_method":      "orb",
                "original_id":       orb_best_entry["id"],
                "original_filename": orb_best_entry.get("filename", "unknown"),
                "thumb_path":        orb_best_entry.get("thumb_path"),
                "debug": {"orb_inliers": orb_best_inliers,
                          "phash_distance": orb_best_ph_dist, "error": str(e)},
            }
        changed_pct = diff["changed_area_pct"]
        largest_pct = diff["largest_region_pct"]
        is_modified = (changed_pct >= modified_area) or (largest_pct >= modified_region)
        return {
            "matched":            True,
            "match_method":       "orb",
            "original_id":        orb_best_entry["id"],
            "original_filename":  orb_best_entry.get("filename", "unknown"),
            "thumb_path":         orb_best_entry.get("thumb_path"),
            "verdict":  "AI-MODIFIED" if is_modified else "REAL",
            "sub_label": (
                "This image differs from a registered original. "
                "The system cannot tell whether the edit was made with AI or manually."
                if is_modified else
                "Registered original \u2014 no significant changes detected."
            ),
            "changed_area_pct":   changed_pct,
            "largest_region_pct": largest_pct,
            "regions":            diff["regions"],
            "debug": {"orb_inliers": orb_best_inliers,
                      "phash_distance": orb_best_ph_dist, "method": "orb"},
        }

    # RULE 3: Face-only match
    if face_best_entry is not None:
        return {
            "matched":            True,
            "match_method":       "face",
            "original_id":        face_best_entry["id"],
            "original_filename":  face_best_entry.get("filename", "unknown"),
            "thumb_path":         face_best_entry.get("thumb_path"),
            "verdict":            "AI-MODIFIED",
            "sub_label": (
                "Same person and pose as a registered original, "
                "but the scene differs. "
                "The system cannot tell AI edits from manual edits."
            ),
            "changed_area_pct":   None,
            "largest_region_pct": None,
            "regions":            [],
            "debug": {**face_best_dbg, "method": "face"},
        }

    # RULE 4: No match
    return no_match
