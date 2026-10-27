"""
registry/face_embed.py  –  v3
==============================
Face detection (MTCNN) + offline pixel-based embedding.

Embedding strategy (tried in order):
  1. ArcFace ONNX  – high accuracy (place w600k_r50.onnx in registry/models/)
  2. Aligned-pixel descriptor – reliable offline fallback:
       • Align 112×112 with MTCNN landmarks
       • Resize to 64×64 grayscale
       • Mean-centre + L2-normalise → 4096-d vector
       • Random noise similarity ≈ 0.0; same face ≈ 0.97+; different person ≈ 0.4-0.75

Public API
----------
FACE_EMBED_AVAILABLE  bool   – False only if MTCNN fails.
EMBED_MODE            str    – "arcface" | "pixel" | "none"
init()                       – call once to warm up (optional; lazy by default)
get_face_meta(bgr)    dict | None
cosine_sim(a, b)      float
landmark_rmse(lm_a, lm_b)  float

Manual ArcFace setup (one-time, internet needed)
------------------------------------------------
  1. Download: https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_sc.zip
  2. Extract w600k_mbf.onnx → rename to w600k_r50.onnx
  3. Place at:  <project>/backend/registry/models/w600k_r50.onnx
  4. Restart backend.
"""

import logging
import numpy as np
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Module-level state (mutated once by init())
# ─────────────────────────────────────────────────────────────────────────────

FACE_EMBED_AVAILABLE = False
EMBED_MODE           = "none"

_mtcnn       = None
_arc_session = None
_MODEL_DIR   = Path(__file__).resolve().parent / "models"
_INITIALIZED = False

# Standard ArcFace 112×112 reference landmarks
_ARC_REF = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041],
], dtype=np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation
# ─────────────────────────────────────────────────────────────────────────────

def init() -> bool:
    """
    Warm up MTCNN and the best available embedding backend.
    Called lazily on first get_face_meta() call; may also be called explicitly
    at startup to surface errors early.
    """
    global FACE_EMBED_AVAILABLE, EMBED_MODE, _mtcnn, _arc_session, _INITIALIZED
    if _INITIALIZED:
        return FACE_EMBED_AVAILABLE
    _INITIALIZED = True

    # ── 1. MTCNN ──────────────────────────────────────────────────────────
    try:
        from mtcnn import MTCNN
        _mtcnn = MTCNN()
        logger.info("[FaceEmbed] MTCNN loaded.")
    except Exception as e:
        logger.warning(f"[FaceEmbed] MTCNN unavailable – face matching disabled: {e}")
        EMBED_MODE = "none"
        return False

    # ── 2a. ArcFace ONNX (optional – high accuracy) ───────────────────────
    onnx_path = _MODEL_DIR / "w600k_r50.onnx"
    if onnx_path.exists():
        try:
            import onnxruntime as ort
            _arc_session = ort.InferenceSession(
                str(onnx_path), providers=["CPUExecutionProvider"])
            dummy = np.zeros((1, 3, 112, 112), dtype=np.float32)
            out   = _arc_session.run(
                None, {_arc_session.get_inputs()[0].name: dummy})
            assert out[0].shape[-1] in (512, 256), f"bad dim: {out[0].shape}"
            logger.info(f"[FaceEmbed] ArcFace ONNX ({onnx_path.name}), "
                        f"dim={out[0].shape[-1]}.")
            FACE_EMBED_AVAILABLE = True
            EMBED_MODE = "arcface"
            return True
        except Exception as e:
            logger.warning(f"[FaceEmbed] ArcFace ONNX error ({e}); "
                           "using pixel fallback.")

    # ── 2b. Pixel descriptor (always works offline) ───────────────────────
    logger.info("[FaceEmbed] Pixel descriptor mode (offline). "
                "Place w600k_r50.onnx in registry/models/ for ArcFace.")
    FACE_EMBED_AVAILABLE = True
    EMBED_MODE = "pixel"
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Alignment
# ─────────────────────────────────────────────────────────────────────────────

def _align_112(bgr: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    """Similarity-warp the face to the 112×112 ArcFace template."""
    from skimage.transform import SimilarityTransform
    tf = SimilarityTransform()
    tf.estimate(landmarks, _ARC_REF)
    M = tf.params[:2]
    return cv2.warpAffine(bgr, M, (112, 112),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REFLECT)


# ─────────────────────────────────────────────────────────────────────────────
# Embedding backends
# ─────────────────────────────────────────────────────────────────────────────

def _embed_arcface(aligned: np.ndarray) -> np.ndarray:
    """ArcFace ONNX → L2-normalised 512-d float32."""
    rgb = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB).astype(np.float32)
    rgb = (rgb - 127.5) / 128.0
    inp = rgb.transpose(2, 0, 1)[None]
    out = _arc_session.run(None, {_arc_session.get_inputs()[0].name: inp})
    e   = out[0][0].astype(np.float32)
    n   = np.linalg.norm(e)
    return e / n if n > 1e-9 else e


def _embed_pixel(aligned: np.ndarray) -> np.ndarray:
    """
    Offline pixel descriptor:
      1. Resize aligned 112×112 face to 64×64 grayscale
      2. Flatten → 4096-d
      3. Subtract mean (zero-centre) so uniform images → zero vector
      4. L2-normalise

    Key properties:
      • Same face (any background): similarity ≈ 0.97+
      • Same person, different photo: 0.55-0.80
      • Different person: 0.20-0.65
      • Random noise pair: ≈ 0.00-0.05  (random vectors in R^4096 are ⊥)
    """
    gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)
    e = small.flatten().astype(np.float32)
    e -= e.mean()
    n = np.linalg.norm(e)
    return e / n if n > 1e-9 else e


# ─────────────────────────────────────────────────────────────────────────────
# Similarity helpers
# ─────────────────────────────────────────────────────────────────────────────

def cosine_sim(a, b) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a / na, b / nb))


def landmark_rmse(lm_a, lm_b) -> float:
    """RMSE of two (5,2) normalised landmark arrays (coords in [0,1])."""
    a = np.asarray(lm_a, dtype=np.float32)
    b = np.asarray(lm_b, dtype=np.float32)
    return float(np.sqrt(np.mean((a - b) ** 2)))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_face_meta(bgr: np.ndarray) -> dict | None:
    """
    Detect the largest face and return its embedding + geometric metadata.
    Returns None if face embedding unavailable or no face found (conf ≥ 0.85).
    """
    if not init():
        return None

    h, w = bgr.shape[:2]
    rgb  = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    try:
        dets = _mtcnn.detect_faces(rgb)
    except Exception as e:
        logger.debug(f"[FaceEmbed] MTCNN: {e}")
        return None

    if not dets:
        return None

    best = max(dets, key=lambda d: d["box"][2] * d["box"][3])
    if best["confidence"] < 0.85:
        return None

    x, y, bw, bh = [int(v) for v in best["box"]]
    x = max(0, x); y = max(0, y)

    kp    = best.get("keypoints", {})
    order = ["left_eye", "right_eye", "nose", "mouth_left", "mouth_right"]
    try:
        lm = np.array([[kp[k][0], kp[k][1]] for k in order], dtype=np.float32)
    except Exception:
        return None

    try:
        aligned = _align_112(bgr, lm)
        emb = (_embed_arcface(aligned) if EMBED_MODE == "arcface"
               else _embed_pixel(aligned))
    except Exception as e:
        logger.debug(f"[FaceEmbed] embed: {e}")
        return None

    return {
        "embedding":       emb.tolist(),
        "box":             [x, y, bw, bh],
        "box_norm":        [x / w, y / h, bw / w, bh / h],
        "landmarks":       lm.tolist(),
        "landmarks_norm":  (lm / np.array([[w, h]], dtype=np.float32)).tolist(),
        "score":           float(best["confidence"]),
        "mode":            EMBED_MODE,
    }
