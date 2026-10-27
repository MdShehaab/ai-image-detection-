"""
test_reference_check.py  –  v3
===============================
Tests the full reference-check pipeline end-to-end.

Registers 5 rich-texture originals, then tests 8 variants each:
  1. same_file         – exact re-upload (must be REAL)
  2. whatsapp_copy     – JPEG Q75 + slight resize (must be REAL)
  3. resized_copy      – 50% scale down + restore (must be REAL)
  4. sunglasses_edit   – sunglasses drawn on face region (must be AI-MODIFIED)
  5. cap_edit          – cap / dark band drawn on top (must be AI-MODIFIED)
  6. bg_change         – background corners replaced (must be AI-MODIFIED)
  7. unrelated_a       – completely different image (must fall back to CNN)
  8. unrelated_b       – another unrelated image (must fall back to CNN)

Verdict mapping:
  matched=True  + verdict=REAL          → "REAL"         (PASS for 1-3)
  matched=True  + verdict=AI-MODIFIED   → "AI-MODIFIED"  (PASS for 4-6)
  matched=False + verdict=None          → "CNN_FALLBACK"  (PASS for 7-8)

Usage:
    python test_reference_check.py

Requires the Flask backend to be running on http://127.0.0.1:5000.
Start it separately with: python run.py
"""

import sys
import io
import time
import requests
import numpy as np
import cv2
from PIL import Image

API     = "http://127.0.0.1:5000/api"
TIMEOUT = 30          # seconds per HTTP request


# ─────────────────────────────────────────────────────────────────────────────
# Image helpers
# ─────────────────────────────────────────────────────────────────────────────

def to_bytes(bgr: np.ndarray, quality: int = 90) -> bytes:
    """BGR → JPEG bytes."""
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    assert ok, "imencode failed"
    return buf.tobytes()


def from_bytes(data: bytes) -> np.ndarray:
    """JPEG bytes → BGR."""
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def whatsapp_copy(bgr: np.ndarray) -> bytes:
    """Simulate WhatsApp re-encoding: Q75 + very slight downscale, then restore."""
    h, w = bgr.shape[:2]
    small = cv2.resize(bgr, (int(w * 0.98), int(h * 0.98)), interpolation=cv2.INTER_AREA)
    back  = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    return to_bytes(back, quality=75)


def resized_copy(bgr: np.ndarray) -> bytes:
    """Resize to 50%, then scale back to original dimensions."""
    h, w = bgr.shape[:2]
    small = cv2.resize(bgr, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    back  = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    return to_bytes(back, quality=85)


def sunglasses_edit(bgr: np.ndarray) -> bytes:
    """Dark sunglasses ellipses in the upper third."""
    edit = bgr.copy()
    h, w = edit.shape[:2]
    cx, cy = w // 2, h // 3
    lw = max(2, w // 45)
    cv2.ellipse(edit, (cx - w // 8, cy), (w // 9, h // 18), 0, 0, 360, (5, 5, 5), -1)
    cv2.ellipse(edit, (cx + w // 8, cy), (w // 9, h // 18), 0, 0, 360, (5, 5, 5), -1)
    cv2.line(edit,   (cx - w // 18, cy), (cx + w // 18, cy), (25, 25, 25), lw)
    # Glasses frame rim
    cv2.ellipse(edit, (cx - w // 8, cy), (w // 9, h // 18), 0, 0, 360, (40, 40, 40), lw)
    cv2.ellipse(edit, (cx + w // 8, cy), (w // 9, h // 18), 0, 0, 360, (40, 40, 40), lw)
    return to_bytes(edit, quality=90)


def cap_edit(bgr: np.ndarray) -> bytes:
    """Dark baseball-cap band across the top 20% of the image."""
    edit = bgr.copy()
    h, w = edit.shape[:2]
    brim_y = int(h * 0.20)
    # Cap body
    cv2.ellipse(edit, (w // 2, brim_y), (w // 2, brim_y // 2), 0, 180, 360, (20, 18, 15), -1)
    # Brim
    brim_pts = np.array([
        [0,         brim_y],
        [w,         brim_y],
        [w + w//8,  brim_y + h//14],
        [-w//8,     brim_y + h//14],
    ], dtype=np.int32)
    cv2.fillPoly(edit, [brim_pts], (30, 28, 22))
    return to_bytes(edit, quality=90)


def bg_change(bgr: np.ndarray) -> bytes:
    """Replace the background corners with a vivid colour gradient."""
    edit = bgr.copy()
    h, w = edit.shape[:2]
    # Create a mask: keep a large central ellipse, replace everything outside
    mask = np.zeros((h, w), np.uint8)
    cv2.ellipse(mask, (w // 2, h // 2), (int(w * 0.38), int(h * 0.38)),
                0, 0, 360, 255, -1)
    # New background: vivid blue-to-purple gradient
    bg = np.zeros_like(edit)
    for y in range(h):
        for x in range(w):
            bg[y, x] = [
                int(220 * x / w),
                int(60 + 60 * y / h),
                int(180 - 80 * x / w),
            ]
    edit[mask == 0] = bg[mask == 0]
    return to_bytes(edit, quality=90)


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic originals  (rich texture so ORB finds keypoints)
# ─────────────────────────────────────────────────────────────────────────────

def _noise(shape, low=0, high=12):
    return np.random.randint(low, high, shape, dtype=np.uint8)


def make_originals(n: int = 5) -> list[np.ndarray]:
    np.random.seed(42)
    imgs = []
    sz   = 512

    for seed in range(n):
        img = np.zeros((sz, sz, 3), np.uint8)

        # ── Base scene ──────────────────────────────────────────────────
        # Sky gradient
        for y in range(sz // 2):
            v = int(80 + seed * 20 + y * 100 / (sz // 2))
            img[y, :] = [
                max(0, min(255, 255 - v)),
                max(0, min(255, 200 - v // 2)),
                max(0, min(255, v)),
            ]
        # Ground
        for y in range(sz // 2, sz):
            img[y, :] = [20 + seed * 5, 80 + seed * 8, 20]

        # Sinusoidal texture on the ground
        for y in range(sz // 2, sz):
            for x in range(sz):
                img[y, x, 1] = int(img[y, x, 1] + 30 * np.sin((x + seed * 40) * 0.08))

        # ── "Person" silhouette ─────────────────────────────────────────
        skin = (180 + seed * 6, 140 + seed * 5, 110 + seed * 4)
        cx   = sz // 2 + (seed - 2) * 30
        # Head
        cv2.ellipse(img, (cx, sz // 3), (sz // 11, sz // 9), 0, 0, 360, skin, -1)
        # Hair
        cv2.ellipse(img, (cx, sz // 4), (sz // 11, sz // 14), 0, 0, 360,
                    (30 + seed * 5, 20, 10), -1)
        # Eyes
        cv2.circle(img, (cx - sz // 22, sz // 3 - sz // 30), sz // 45, (20, 15, 10), -1)
        cv2.circle(img, (cx + sz // 22, sz // 3 - sz // 30), sz // 45, (20, 15, 10), -1)
        # Body
        shirt_col = [(80, 60, 200), (200, 80, 60), (60, 200, 80),
                     (200, 200, 60), (60, 200, 200)][seed % 5]
        cv2.rectangle(img,
                      (cx - sz // 13, sz // 3 + sz // 11),
                      (cx + sz // 13, 3 * sz // 4),
                      shirt_col, -1)

        # ── Sharp textures for ORB keypoints ───────────────────────────
        # High-contrast grid in corner
        for gy in range(10, 80, 12):
            for gx in range(10, 80, 12):
                cv2.rectangle(img, (gx, gy), (gx + 6, gy + 6),
                              (200 + seed * 10, 50, 50 + seed * 30), -1)
        # Bottom-right checkerboard strip
        for bx in range(sz - 80, sz, 10):
            for by in range(sz - 30, sz, 10):
                v = 220 if ((bx + by) // 10) % 2 == 0 else 30
                img[by: by + 10, bx: bx + 10] = [v, v // 2, 255 - v]

        img = cv2.add(img, _noise(img.shape))
        imgs.append(img)

    return imgs
def make_unrelated_images(n: int = 2) -> list[np.ndarray]:
    """
    Generate truly unrelated images: completely different content, colors and
    structure from the face/scene originals so phash distance >> 20.
    """
    np.random.seed(99)
    imgs = []
    sz   = 512

    # 1. Perlin-like abstract noise field (no faces, no sky, no ground)
    img = np.zeros((sz, sz, 3), np.uint8)
    x = np.linspace(0, 8 * np.pi, sz, dtype=np.float32)
    y = np.linspace(0, 8 * np.pi, sz, dtype=np.float32)
    xv, yv = np.meshgrid(x, y)
    ch0 = ((np.sin(xv * 1.3) * np.cos(yv * 0.7) + 1) * 127).astype(np.uint8)
    ch1 = ((np.sin(xv * 0.4 + yv * 1.1) + 1) * 127).astype(np.uint8)
    ch2 = ((np.cos(xv * 2.1 - yv * 0.9) + 1) * 127).astype(np.uint8)
    imgs.append(cv2.merge([ch0, ch1, ch2]))

    # 2. Coloured frequency stripes + random blobs
    img = np.zeros((sz, sz, 3), np.uint8)
    for row in range(sz):
        img[row, :] = [
            max(0, min(255, int(128 + 127 * np.sin(row * 0.15)))),
            max(0, min(255, int(128 + 127 * np.cos(row * 0.22)))),
            max(0, min(255, int(60  + 80  * np.sin(row * 0.09 + 1.5)))),
        ]
    # Overlay random blobs of solid colour
    rng = np.random.default_rng(seed=77)
    for _ in range(12):
        cx = rng.integers(60, sz - 60)
        cy = rng.integers(60, sz - 60)
        r  = rng.integers(20, 60)
        col = tuple(int(c) for c in rng.integers(0, 255, 3))
        cv2.circle(img, (cx, cy), r, col, -1)
    imgs.append(img)

    # Return only requested count
    return imgs[:n]



def clean_registry():
    try:
        r = requests.get(f"{API}/registry", timeout=TIMEOUT)
        r.raise_for_status()
        for e in r.json().get("entries", []):
            requests.delete(f"{API}/registry/{e['id']}", timeout=TIMEOUT)
        print(f"  Cleaned {len(r.json().get('entries', []))} stale entries.")
    except Exception as ex:
        print(f"  Registry cleanup: {ex}")


def register(bgr: np.ndarray, name: str) -> str:
    data = to_bytes(bgr, quality=95)
    r = requests.post(
        f"{API}/registry/register",
        files={"file": (name, data, "image/jpeg")},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["entry"]["id"]


def detect(data: bytes, name: str) -> dict:
    r = requests.post(
        f"{API}/detect/image",
        files={"file": (name, data, "image/jpeg")},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 88)
    print("  REFERENCE CHECK TEST SUITE  v3")
    print("=" * 88)
    print(f"\nBackend : {API}")
    print("Verdicts: REAL (inliers+phash, no sig change), AI-MODIFIED (change detected),")
    print("          CNN_FALLBACK (no registry match)")
    print()

    print("Cleaning registry ...")
    clean_registry()
    print()

    originals = make_originals(5)
    unrelated  = make_unrelated_images(2)   # truly different content

    ids = []
    print("Registering 5 originals ...")
    for i, img in enumerate(originals):
        eid = register(img, f"original_{i+1}.jpg")
        ids.append(eid)
        print(f"  [{i+1}] id={eid[:8]}...")
    print()

    VARIANTS = [
        ("same_file",      lambda img: to_bytes(img, 95)),
        ("whatsapp_copy",  whatsapp_copy),
        ("resized_copy",   resized_copy),
        ("sunglasses_edit",sunglasses_edit),
        ("cap_edit",       cap_edit),
        ("bg_change",      bg_change),
        ("unrelated_a",    lambda img: to_bytes(unrelated[0], 90)),
        ("unrelated_b",    lambda img: to_bytes(unrelated[1], 90)),
    ]

    EXPECTED = {
        "same_file":       "REAL",
        "whatsapp_copy":   "REAL",
        "resized_copy":    "REAL",
        "sunglasses_edit": "AI-MODIFIED",
        "cap_edit":        "AI-MODIFIED",
        "bg_change":       "AI-MODIFIED",
        "unrelated_a":     "CNN_FALLBACK",
        "unrelated_b":     "CNN_FALLBACK",
    }

    header = (f"{'#':<3} {'Variant':<18} {'Verdict':<14} {'orb':>5} {'phash':>6} "
              f"{'chg%':>7} {'lgr%':>7}  result")
    print(header)
    print("-" * len(header))

    rows = []
    for i, img in enumerate(originals):
        for vname, fn in VARIANTS:
            try:
                data = fn(img)
                resp = detect(data, f"orig{i+1}_{vname}.jpg")

                rc  = resp.get("reference_check", {})
                dbg = rc.get("debug", {})
                matched = rc.get("matched", False)
                verdict = rc.get("verdict")

                if matched and verdict == "REAL":
                    got = "REAL"
                elif matched and verdict == "AI-MODIFIED":
                    got = "AI-MODIFIED"
                else:
                    got = "CNN_FALLBACK"

                exp      = EXPECTED[vname]
                ok       = got == exp
                orb      = dbg.get("orb_inliers",   "?")
                ph       = dbg.get("phash_distance", "?")
                chg      = rc.get("changed_area_pct")
                lgr      = rc.get("largest_region_pct")
                chg_s    = f"{chg:.3f}" if chg is not None else "    —"
                lgr_s    = f"{lgr:.3f}" if lgr is not None else "    —"
                status   = "PASS" if ok else "FAIL"

                print(f"{i+1:<3} {vname:<18} {got:<14} {str(orb):>5} {str(ph):>6} "
                      f"{chg_s:>7} {lgr_s:>7}  [{status}] expected={exp}")
                rows.append((i + 1, vname, got, exp, ok, orb, ph, chg, lgr))
            except Exception as e:
                print(f"{i+1:<3} {vname:<18} ERROR: {e}")
                rows.append((i + 1, vname, "ERROR", EXPECTED[vname], False, None, None, None, None))

        print()

    # ── Summary ─────────────────────────────────────────────────────────────
    total  = len(rows)
    passed = sum(1 for r in rows if r[4])

    print("=" * 88)
    print("  SUMMARY TABLE")
    print("=" * 88)
    print(f"{'Variant':<18} {'Pass':>5} {'Fail':>5}")
    print("-" * 34)
    for vname, _ in VARIANTS:
        vrows = [r for r in rows if r[1] == vname]
        p = sum(1 for r in vrows if r[4])
        f = len(vrows) - p
        print(f"  {vname:<16} {p:>5} {f:>5}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print()
    print("Threshold configuration:")
    print("  ORB inlier threshold        : 15")
    print("  phash Hamming threshold     : 20")
    print("  diff amplitude cutoff       : 25  (JPEG/resize noise floor)")
    print("  MODIFIED area threshold     : 0.4%  (changed_area_pct >= this)")
    print("  MODIFIED region threshold   : 0.15% (largest single region >= this)")

    if passed < total:
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
