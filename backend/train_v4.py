"""
train_v4.py -- EfficientNetB0 Training with Random-Scale Crop Augmentation
==========================================================================
Changes vs. model_v2 (train_image_classifier.py):
  * load_and_preprocess_image_v4() adds a random-scale crop BEFORE the
    existing flip/rotate/JPEG/brightness augmentation (training only).
  * Random crop scale: uniform in [0.50, 1.00] of both image dimensions.
  * Random crop position: uniformly random x/y offset (not centered).
  * Applied to ALL classes equally so crop-scale cannot be a class signal.
  * Validation and test images: unchanged full-frame resize as before.
  * Architecture, class weights, phase structure: identical to model_v2.
  * Output: model_v4.keras in the same weights directory.
  * After epoch 1, timing is printed so you can abort if speed regressed.

Usage (Phase 1 only, 3 epochs, same as model_v2):
    cd backend
    python train_v4.py
    python train_v4.py --phase1_epochs 3 --phase2_epochs 0
    python train_v4.py --batch_size 64 --phase1_epochs 3 --phase2_epochs 0
"""
import sys as _sys
if hasattr(_sys.stdout, 'reconfigure'):
    try:
        _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
del _sys


import os
import sys
import time
import argparse
import random
import json
import threading
from pathlib import Path

import numpy as np
import pandas as pd
import cv2
import tensorflow as tf

# -----------------------------------------------------------------------------
# 1. CONFIG
# -----------------------------------------------------------------------------

def is_running_in_colab() -> bool:
    try:
        import google.colab
        return True
    except ImportError:
        return False


def resolve_base_data_dir(cli_path: str = None) -> Path:
    if cli_path:
        return Path(cli_path).resolve()
    if is_running_in_colab():
        local_colab = Path("/content/datasets")
        if local_colab.exists():
            return local_colab
        return Path("/content/drive/MyDrive/deepfake_project/datasets")
    candidates = [
        Path("./datasets").resolve(),
        Path(r"C:\Users\sheha\OneDrive\Desktop\AI-Powered Visual Deepfake Detection and Analysis System\datasets").resolve(),
        Path(r"..\datasets").resolve(),
        Path(r"c:\Users\sheha\OneDrive\Desktop\new project\datasets").resolve(),
    ]
    for cp in candidates:
        if (cp / "processed_3class").exists() or (cp.parent / "dataset" / "image_detection").exists():
            return cp
    return Path("./datasets").resolve()


CLASS_TO_IDX  = {"ai_generated": 0, "ai_modified": 1, "real": 2}
IDX_TO_CLASS  = {v: k for k, v in CLASS_TO_IDX.items()}
CLASS_WEIGHTS = {0: 1.45, 1: 1.52, 2: 1.00}

_thread_local = threading.local()


def get_face_cascade():
    if not hasattr(_thread_local, "cascade"):
        _thread_local.cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    return _thread_local.cascade


def resolve_image_path(base_dir: Path, rel_path: str) -> Path:
    p = base_dir / rel_path
    if p.exists():
        return p
    if "image_detection" in rel_path:
        p2 = base_dir.parent / "dataset" / rel_path
        if p2.exists():
            return p2
        p3 = base_dir / rel_path.replace("image_detection/", "")
        if p3.exists():
            return p3
    return p


# -----------------------------------------------------------------------------
# 2. PREPROCESSING  --  v4 adds random-scale crop for training images
# -----------------------------------------------------------------------------

def _random_scale_crop(img_bgr: np.ndarray) -> np.ndarray:
    """
    [NEW in v4] Apply a random-scale crop to img_bgr (BGR numpy array).

    Algorithm:
        1. Pick crop_scale ~ Uniform[0.50, 1.00].
        2. Compute crop_h = int(h * crop_scale), crop_w = int(w * crop_scale).
        3. Pick random top-left corner: x0 ~ Uniform[0, w - crop_w],
                                        y0 ~ Uniform[0, h - crop_h].
        4. Return the cropped sub-image (NOT resized here -- caller resizes to 224x224).

    * No face detector involved -- pure arithmetic on array indices, very fast.
    * Applied ONLY on the training path; val/test bypass this function entirely.
    * Applied to ALL classes equally.
    """
    h, w = img_bgr.shape[:2]

    # Guarantee a minimum crop of 2x2 pixels even on tiny images
    crop_scale = random.uniform(0.50, 1.00)
    crop_h = max(2, int(h * crop_scale))
    crop_w = max(2, int(w * crop_scale))

    # Random offset within valid range (always >= 0 since crop_dim <= dim)
    y0 = random.randint(0, h - crop_h)
    x0 = random.randint(0, w - crop_w)

    return img_bgr[y0: y0 + crop_h, x0: x0 + crop_w]


def load_and_preprocess_image_v4(
    base_data_dir: Path,
    image_rel_path: str,
    source_dataset: str,
    is_training: bool = False,
    target_size: tuple = (224, 224),
) -> np.ndarray:
    """
    v4 preprocessing -- identical contract as original except:
    * Training images get a random-scale crop BEFORE resize and augmentation.
    * Val/test images are unchanged (full-frame resize, same as model_v2).

    Execution order for training images:
        1. [NEW] Random-scale crop  (scale in [0.50, 1.00], random x/y position)
        2. Resize to 224x224  (same as before -- now resizes the crop)
        3. Horizontal flip (p=0.5)
        4. Rotation +/-10deg
        5. JPEG re-encode at random quality 70-95
        6. Brightness/contrast jitter

    Note: FaceForensics++ Haar-cascade face crop is applied FIRST (before the
    random crop) on that dataset only, matching the original pipeline exactly.
    """
    abs_path = resolve_image_path(base_data_dir, image_rel_path)
    if not abs_path.exists():
        return np.zeros((target_size[0], target_size[1], 3), dtype=np.float32)

    img_bgr = cv2.imread(str(abs_path))
    if img_bgr is None:
        return np.zeros((target_size[0], target_size[1], 3), dtype=np.float32)

    h, w, _ = img_bgr.shape

    # -- Branch 1: FaceForensics++ (Haar face crop, same as original) ----------
    if "faceforensics" in source_dataset.lower():
        face_cascade = get_face_cascade()
        scale = 320.0 / max(h, w)
        if scale < 1.0:
            thumb_w, thumb_h = int(w * scale), int(h * scale)
            thumb = cv2.resize(img_bgr, (thumb_w, thumb_h), interpolation=cv2.INTER_NEAREST)
            gray = cv2.cvtColor(thumb, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))
            inv = 1.0 / scale
            scaled_faces = [[int(x*inv), int(y*inv), int(fw*inv), int(fh*inv)] for x, y, fw, fh in faces]
        else:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            scaled_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))

        if len(scaled_faces) > 0:
            fx, fy, fw, fh = max(scaled_faces, key=lambda b: b[2] * b[3])
            mx, my = int(0.20 * fw), int(0.20 * fh)
            x1, y1 = max(0, fx - mx), max(0, fy - my)
            x2, y2 = min(w, fx + fw + mx), min(h, fy + fh + my)
            cropped = img_bgr[y1:y2, x1:x2]
        else:
            min_dim = min(h, w)
            sy, sx = (h - min_dim) // 2, (w - min_dim) // 2
            cropped = img_bgr[sy: sy + min_dim, sx: sx + min_dim]

        # [NEW v4] Random-scale crop on top of the face crop (training only)
        if is_training:
            cropped = _random_scale_crop(cropped)

        resized = cv2.resize(cropped, target_size, interpolation=cv2.INTER_LINEAR)

    # -- Branch 2: All other datasets -----------------------------------------
    else:
        if is_training:
            # [NEW v4] Random-scale crop BEFORE resize
            img_bgr = _random_scale_crop(img_bgr)

        resized = cv2.resize(img_bgr, target_size, interpolation=cv2.INTER_LINEAR)

    # -- Augmentation (train split only) -- unchanged from original ------------
    if is_training:
        # Horizontal flip
        if random.random() > 0.5:
            resized = cv2.flip(resized, 1)
        # Rotation +/-10deg
        angle = random.uniform(-10, 10)
        M = cv2.getRotationMatrix2D((target_size[0] / 2, target_size[1] / 2), angle, 1.0)
        resized = cv2.warpAffine(resized, M, target_size, borderMode=cv2.BORDER_REFLECT)
        # JPEG quality jitter (compression robustness)
        quality = random.randint(70, 95)
        _, enc = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        resized = cv2.imdecode(enc, 1)
        # Brightness / contrast jitter
        alpha = random.uniform(0.9, 1.1)
        beta  = random.uniform(-15, 15)
        resized = cv2.convertScaleAbs(resized, alpha=alpha, beta=beta)

    img_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    return img_rgb.astype(np.float32)


# -----------------------------------------------------------------------------
# 3. tf.data PIPELINE
# -----------------------------------------------------------------------------

def build_tf_data_pipeline_v4(
    df: pd.DataFrame,
    base_data_dir: Path,
    batch_size: int = 64,
    is_training: bool = False,
) -> tf.data.Dataset:
    """High-throughput multi-core tf.data pipeline using v4 preprocessor."""
    image_paths    = df["image_path"].values.astype(str)
    source_datasets = df["source_dataset"].values.astype(str)
    labels         = df["class"].map(CLASS_TO_IDX).values.astype(np.int32)

    ds = tf.data.Dataset.from_tensor_slices((image_paths, source_datasets, labels))
    if is_training:
        ds = ds.shuffle(buffer_size=min(len(df), 4096), reshuffle_each_iteration=True)

    def _py_loader(p_bytes, s_bytes, is_train_bool):
        p_str = p_bytes.numpy().decode("utf-8")
        s_str = s_bytes.numpy().decode("utf-8")
        return load_and_preprocess_image_v4(
            base_data_dir, p_str, s_str, is_training=bool(is_train_bool)
        )

    def _map_fn(p, s, l):
        img = tf.py_function(func=_py_loader, inp=[p, s, is_training], Tout=tf.float32)
        img.set_shape([224, 224, 3])
        l.set_shape([])
        return img, l

    ds = ds.map(_map_fn, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size, drop_remainder=False)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


# -----------------------------------------------------------------------------
# 4. MODEL -- identical architecture to model_v2
# -----------------------------------------------------------------------------

def build_efficientnet_model(input_shape=(224, 224, 3), num_classes=3):
    base_model = tf.keras.applications.EfficientNetB0(
        weights="imagenet", include_top=False, input_shape=input_shape
    )
    x       = tf.keras.layers.GlobalAveragePooling2D(name="avg_pool")(base_model.output)
    x       = tf.keras.layers.Dense(256, activation="relu", name="dense_256")(x)
    x       = tf.keras.layers.Dropout(0.3, name="dropout_0.3")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="predictions")(x)
    return tf.keras.Model(inputs=base_model.input, outputs=outputs, name="EfficientNetB0_v4"), base_model


# -----------------------------------------------------------------------------
# 5. REAL-PHOTO RETEST  (shehaab.jpg + group photos from uploads/)
# -----------------------------------------------------------------------------

def retest_real_photos(model, weights_dir: Path, backend_dir: Path):
    """
    Re-run inference on the specific real photos that model_v2 got wrong,
    using the new v4 weights and the same calibrated prediction pipeline.
    Photos are taken from the uploads/ folder (session copies) and Downloads/.
    """
    CANDIDATE_PATHS = [
        backend_dir / "uploads" / "a40e90bd3124_shehaab.jpg",        # portrait -- was REAL [OK] by v2
        backend_dir / "uploads" / "6e2c3728583f_1.jpg",               # group -- was REAL [OK] by v2
        backend_dir / "uploads" / "cf8c10b57529_download_2.jpg",      # group -- was REAL [OK] by v2
        Path(r"C:\Users\sheha\Downloads\shehaab.jpg"),
        Path(r"C:\Users\sheha\Downloads\1.jpg"),
        Path(r"C:\Users\sheha\Downloads\2.jpg"),
        Path(r"C:\Users\sheha\Downloads\3.jpg"),
        Path(r"C:\Users\sheha\Downloads\download (2).jpg"),
    ]

    photos = []
    seen   = set()
    for p in CANDIDATE_PATHS:
        ap = p.resolve()
        if ap.exists() and str(ap) not in seen:
            photos.append(ap)
            seen.add(str(ap))

    if not photos:
        print("[INFO] No real-photo retest candidates found -- skipping.")
        return

    CLASS_MAP     = {0: "ai_generated", 1: "ai_modified", 2: "real"}
    FAKE_THRESHOLD = 0.70
    CW            = np.array([1.45, 1.52, 1.00], dtype=np.float32)

    print("\n" + "=" * 80)
    print("  REAL-PHOTO RETEST  (v4 model vs v2 baseline)")
    print("=" * 80)
    print(f"  {'Photo':<40} | {'v4 Verdict':<14} | {'Conf':>7} | P(real) | P(fake)")
    print(f"  {'-'*80}")

    results = []
    for photo_path in photos:
        img_bgr = cv2.imread(str(photo_path))
        if img_bgr is None:
            continue
        resized  = cv2.resize(img_bgr, (224, 224), interpolation=cv2.INTER_LINEAR)
        img_rgb  = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32)
        tensor   = np.expand_dims(img_rgb, axis=0)

        raw      = model.predict(tensor, verbose=0)[0]
        cal      = raw / CW
        cal     /= cal.sum()

        p_gen, p_mod, p_real = float(cal[0]), float(cal[1]), float(cal[2])
        fake_p = p_gen + p_mod

        if fake_p >= FAKE_THRESHOLD:
            top_idx  = 0 if p_gen > p_mod else 1
            verdict  = "AI-MODIFIED"
            conf     = float(cal[top_idx]) * 100
        else:
            verdict  = "REAL"
            conf     = p_real * 100

        icon = "[OK]" if verdict == "REAL" else "[X]"
        name = photo_path.name[:38]
        print(f"  {name:<40} | {icon} {verdict:<12} | {conf:>6.2f}% | {p_real:.4f} | {fake_p:.4f}")
        results.append({
            "photo": photo_path.name,
            "verdict": verdict,
            "confidence": round(conf, 2),
            "p_real": round(p_real, 4),
            "p_fake": round(fake_p, 4),
        })

    print()
    return results


# -----------------------------------------------------------------------------
# 6. MAIN TRAINING + EVALUATION LOOP
# -----------------------------------------------------------------------------

def train_v4(
    manifest_path: str = None,
    data_dir: str      = None,
    output_dir: str    = None,
    batch_size: int    = 64,
    phase1_epochs: int = 3,
    phase2_epochs: int = 0,
    sample_limit: int  = None,
    abort_after_epoch1_if_slow: bool = True,
    slow_threshold_seconds: float    = 900.0,   # 15 min -> definitely too slow
):
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    start_total = time.time()

    # -- Paths ----------------------------------------------------------------
    base_data_dir  = resolve_base_data_dir(data_dir)
    manifest_file  = Path(manifest_path).resolve() if manifest_path else base_data_dir / "manifest_combined.csv"
    if not manifest_file.exists():
        # Try common locations relative to this script's parent (project root)
        backend_dir_tmp = Path(__file__).parent.resolve()
        for candidate in [
            backend_dir_tmp.parent / "datasets" / "manifest_combined.csv",
            backend_dir_tmp / "datasets" / "manifest_combined.csv",
            Path("./datasets/manifest_combined.csv").resolve(),
        ]:
            if candidate.exists():
                manifest_file = candidate
                break

    backend_dir = Path(__file__).parent.resolve()

    if output_dir:
        out_path = Path(output_dir).resolve()
    elif is_running_in_colab():
        out_path = Path("/content/drive/MyDrive/deepfake_project/outputs")
    else:
        out_path = backend_dir / "models" / "image_detector" / "weights"

    out_path.mkdir(parents=True, exist_ok=True)
    reports_path = Path("./reports").resolve() if not is_running_in_colab() else out_path
    reports_path.mkdir(parents=True, exist_ok=True)

    v4_model_path = out_path / "model_v4.keras"

    # -- Banner ---------------------------------------------------------------
    print("=" * 80)
    print("  EfficientNetB0 v4 -- Random-Scale Crop Augmentation Training")
    print("=" * 80)
    print(f"  Augmentation     : random crop scale in [0.50, 1.00] + random position")
    print(f"  Applied to       : ALL classes, training split only")
    print(f"  Architecture     : identical to model_v2")
    print(f"  Class weights    : {CLASS_WEIGHTS}")
    print(f"  Base data dir    : {base_data_dir}")
    print(f"  Manifest         : {manifest_file}")
    print(f"  Output           : {v4_model_path}")
    print(f"  Phase 1 epochs   : {phase1_epochs}  (head training, base frozen)")
    print(f"  Phase 2 epochs   : {phase2_epochs}  (fine-tune top 30)")
    print(f"  Batch size       : {batch_size}")
    gpus = tf.config.list_physical_devices("GPU")
    print(f"  Hardware         : {'GPU -> ' + gpus[0].name if gpus else 'CPU (multi-core tf.data)'}")
    print()

    # -- Dataset --------------------------------------------------------------
    df = pd.read_csv(manifest_file)
    print(f"  Manifest loaded  : {len(df):,} total rows")

    if sample_limit:
        train_df = df[df["split"] == "train"].sample(n=min(sample_limit, len(df[df["split"] == "train"])), random_state=42)
        val_df   = df[df["split"] == "validation"].sample(n=min(sample_limit // 4, len(df[df["split"] == "validation"])), random_state=42)
        test_df  = df[df["split"] == "test"].sample(n=min(sample_limit // 4, len(df[df["split"] == "test"])), random_state=42)
    else:
        train_df = df[df["split"] == "train"].reset_index(drop=True)
        val_df   = df[df["split"] == "validation"].reset_index(drop=True)
        test_df  = df[df["split"] == "test"].reset_index(drop=True)

    print(f"  Train / Val / Test : {len(train_df):,} / {len(val_df):,} / {len(test_df):,}")
    print()

    train_ds = build_tf_data_pipeline_v4(train_df, base_data_dir, batch_size=batch_size, is_training=True)
    val_ds   = build_tf_data_pipeline_v4(val_df,   base_data_dir, batch_size=batch_size, is_training=False)
    test_ds  = build_tf_data_pipeline_v4(test_df,  base_data_dir, batch_size=batch_size, is_training=False)

    model, base_model = build_efficientnet_model()
    best_val_acc      = 0.0
    batch_count       = int(np.ceil(len(train_df) / batch_size))

    # -- PHASE 1: Frozen base head training -----------------------------------
    print("=" * 80)
    print(f"  PHASE 1  -- Head training ({phase1_epochs} epoch{'s' if phase1_epochs != 1 else ''}), base frozen, LR=1e-3")
    print("=" * 80)
    base_model.trainable = False
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    for epoch in range(phase1_epochs):
        ep_start = time.time()
        tr_losses, tr_accs, data_times, comp_times = [], [], [], []
        ds_iter = iter(train_ds)

        for b_idx in range(batch_count):
            t0 = time.time()
            X_b, y_b = next(ds_iter)
            data_times.append(time.time() - t0)

            t0 = time.time()
            loss, acc = model.train_on_batch(X_b, y_b, class_weight=CLASS_WEIGHTS)
            comp_times.append(time.time() - t0)

            tr_losses.append(loss)
            tr_accs.append(acc)

            if (b_idx + 1) % 25 == 0 or (b_idx + 1) == batch_count:
                print(
                    f"  P1 Epoch [{epoch+1}/{phase1_epochs}] "
                    f"Batch [{b_idx+1}/{batch_count}] "
                    f"Data:{np.mean(data_times)*1000:5.1f}ms "
                    f"Compute:{np.mean(comp_times)*1000:5.1f}ms "
                    f"Loss:{loss:.4f} Acc:{acc*100:.1f}%",
                    end="\r",
                )

        # Validation pass
        val_losses, val_accs = [], []
        for X_b, y_b in val_ds:
            vl, va = model.test_on_batch(X_b, y_b)
            val_losses.append(vl)
            val_accs.append(va)

        ep_dur = time.time() - ep_start
        mean_tr_loss  = float(np.mean(tr_losses))
        mean_tr_acc   = float(np.mean(tr_accs))
        mean_val_loss = float(np.mean(val_losses))
        mean_val_acc  = float(np.mean(val_accs))
        avg_data_ms   = float(np.mean(data_times)) * 1000
        avg_comp_ms   = float(np.mean(comp_times)) * 1000

        print(
            f"\n  Epoch {epoch+1} done  {ep_dur:.1f}s | "
            f"Train {mean_tr_loss:.4f}/{mean_tr_acc*100:.2f}%  "
            f"Val {mean_val_loss:.4f}/{mean_val_acc*100:.2f}%  "
            f"[Data:{avg_data_ms:.1f}ms  Compute:{avg_comp_ms:.1f}ms per batch avg]"
        )

        # -- Epoch-1 timing gate -------------------------------------------
        if epoch == 0:
            print(f"\n  +- TIMING CHECK AFTER EPOCH 1 -------------------------+")
            print(f"  |  Epoch wall-clock time : {ep_dur:.1f}s                    |")
            print(f"  |  Avg data load/batch   : {avg_data_ms:.1f} ms              |")
            print(f"  |  Avg model compute/btch: {avg_comp_ms:.1f} ms              |")
            if ep_dur <= slow_threshold_seconds:
                print(f"  |  [OK] Speed OK -- continuing all {phase1_epochs} epochs.         |")
            else:
                print(f"  |  [!]  Epoch too slow ({ep_dur:.0f}s > {slow_threshold_seconds:.0f}s threshold).  |")
                if abort_after_epoch1_if_slow:
                    print(f"  |  Aborting. Reduce batch_size or use --sample_limit.   |")
                    print(f"  +------------------------------------------------------+\n")
                    model.save(out_path / "model_v4_epoch1_only.keras")
                    print(f"  [INFO] Epoch-1 checkpoint saved -> model_v4_epoch1_only.keras")
                    return
            print(f"  +------------------------------------------------------+\n")

        # Save per-epoch checkpoint
        ckpt_path = out_path / f"v4_checkpoint_p1_epoch{epoch+1}.keras"
        model.save(ckpt_path)
        if mean_val_acc > best_val_acc:
            best_val_acc = mean_val_acc
            model.save(v4_model_path)
            print(f"  [+] New best val acc {best_val_acc*100:.2f}% -> saved {v4_model_path.name}")

    # -- PHASE 2: Fine-tune top 30 layers -------------------------------------
    if phase2_epochs > 0:
        print("\n" + "=" * 80)
        print(f"  PHASE 2  -- Fine-tune top 30 layers ({phase2_epochs} epoch{'s' if phase2_epochs!=1 else ''}), LR=1e-5")
        print("=" * 80)
        base_model.trainable = True
        for layer in base_model.layers[:-30]:
            layer.trainable = False
        for layer in base_model.layers[-30:]:
            layer.trainable = True

        model.compile(
            optimizer=tf.keras.optimizers.Adam(1e-5),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        for epoch in range(phase2_epochs):
            ep_start = time.time()
            tr_losses, tr_accs, data_times, comp_times = [], [], [], []
            ds_iter = iter(train_ds)

            for b_idx in range(batch_count):
                t0 = time.time()
                X_b, y_b = next(ds_iter)
                data_times.append(time.time() - t0)

                t0 = time.time()
                loss, acc = model.train_on_batch(X_b, y_b, class_weight=CLASS_WEIGHTS)
                comp_times.append(time.time() - t0)

                tr_losses.append(loss)
                tr_accs.append(acc)

                if (b_idx + 1) % 25 == 0 or (b_idx + 1) == batch_count:
                    print(
                        f"  P2 Epoch [{epoch+1}/{phase2_epochs}] "
                        f"Batch [{b_idx+1}/{batch_count}] "
                        f"Data:{np.mean(data_times)*1000:5.1f}ms "
                        f"Compute:{np.mean(comp_times)*1000:5.1f}ms "
                        f"Loss:{loss:.4f} Acc:{acc*100:.1f}%",
                        end="\r",
                    )

            val_losses, val_accs = [], []
            for X_b, y_b in val_ds:
                vl, va = model.test_on_batch(X_b, y_b)
                val_losses.append(vl)
                val_accs.append(va)

            ep_dur = time.time() - ep_start
            mean_val_acc = float(np.mean(val_accs))
            print(
                f"\n  Epoch {epoch+1} done  {ep_dur:.1f}s | "
                f"Train {np.mean(tr_losses):.4f}/{np.mean(tr_accs)*100:.2f}%  "
                f"Val {np.mean(val_losses):.4f}/{mean_val_acc*100:.2f}%"
            )

            ckpt_path = out_path / f"v4_checkpoint_p2_epoch{epoch+1}.keras"
            model.save(ckpt_path)
            if mean_val_acc > best_val_acc:
                best_val_acc = mean_val_acc
                model.save(v4_model_path)
                print(f"  [+] New best -> {v4_model_path.name}  val_acc={best_val_acc*100:.2f}%")

    # -- Load best checkpoint for evaluation ----------------------------------
    if v4_model_path.exists():
        model = tf.keras.models.load_model(v4_model_path)
        print(f"\n  [*] Loaded best checkpoint (val_acc={best_val_acc*100:.2f}%) for evaluation.")

    # -- TEST SPLIT EVALUATION -------------------------------------------------
    print("\n" + "=" * 80)
    print("  FINAL TEST SPLIT EVALUATION -- model_v4")
    print("=" * 80)

    y_true_all, y_pred_probs_all = [], []
    for X_b, y_b in test_ds:
        probs = model.predict(X_b, verbose=0)
        y_pred_probs_all.append(probs)
        y_true_all.append(y_b.numpy())

    y_true  = np.concatenate(y_true_all)
    y_probs = np.concatenate(y_pred_probs_all)
    y_preds = np.argmax(y_probs, axis=1)

    overall_acc  = float(np.mean(y_preds == y_true) * 100)
    target_names = [IDX_TO_CLASS[i] for i in range(3)]

    print(f"\n  Overall Test Accuracy : {overall_acc:.2f}%\n")
    cls_report      = classification_report(y_true, y_preds, target_names=target_names, digits=4, zero_division=0)
    cls_report_dict = classification_report(y_true, y_preds, target_names=target_names, digits=4, output_dict=True, zero_division=0)
    print(cls_report)

    cm = confusion_matrix(y_true, y_preds, labels=[0, 1, 2])
    print("  3x3 Confusion Matrix:")
    header = f"  {'True \\ Pred':<16}" + "".join([f"{c:<16}" for c in target_names])
    print(header)
    for i, row in enumerate(cm):
        print(f"  {target_names[i]:<16}" + "".join([f"{v:<16}" for v in row]))

    cm_path = reports_path / "v4_confusion_matrix.png"
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=target_names, yticklabels=target_names)
    plt.title(f"EfficientNetB0 v4 Confusion Matrix (Test Acc: {overall_acc:.2f}%)")
    plt.ylabel("True Class")
    plt.xlabel("Predicted Class")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=150)
    plt.close()
    print(f"\n  Confusion matrix saved -> {cm_path}")

    y_true_oh = np.eye(3)[y_true.astype(int)]
    roc_auc   = float(roc_auc_score(y_true_oh, y_probs, multi_class="ovr"))
    print(f"  ROC-AUC (OvR): {roc_auc:.4f}")

    # Sub-dataset breakdown
    print("\n  Sub-Dataset Accuracy Breakdown:")
    test_df_copy = test_df.copy()
    test_df_copy["y_true"] = y_true
    test_df_copy["y_pred"] = y_preds
    test_df_copy["correct"] = test_df_copy["y_true"] == test_df_copy["y_pred"]
    subdataset_metrics = {}
    for src, grp in test_df_copy.groupby("source_dataset"):
        acc_pct = float(grp["correct"].mean() * 100)
        subdataset_metrics[src] = {"accuracy_pct": round(acc_pct, 2), "n": len(grp)}
        print(f"    {src:<40}: {acc_pct:.2f}% ({grp['correct'].sum()}/{len(grp)})")

    # High-stakes error analysis
    manip_as_real = int(cm[1][2])
    real_as_manip = int(cm[2][1])
    total_manip   = int(np.sum(cm[1]))
    fn_rate       = round(manip_as_real / max(1, total_manip) * 100, 2)
    print(f"\n  [!] AI_MODIFIED -> REAL (false negatives): {manip_as_real}/{total_manip} ({fn_rate}%)")
    print(f"  [!] REAL -> AI_MODIFIED (false positives): {real_as_manip}/{int(np.sum(cm[2]))}")

    # -- REAL-PHOTO RETEST -----------------------------------------------------
    retest_results = retest_real_photos(model, out_path, backend_dir)

    # -- Save metadata ---------------------------------------------------------
    metadata = {
        "model_name":       "EfficientNetB0_v4_RandomScaleCrop",
        "version":          "v4",
        "augmentation":     "random_scale_crop_0.5_1.0 + flip + rotate + jpeg + brightness",
        "classes":          ["ai_generated", "ai_modified", "real"],
        "class_to_idx":     CLASS_TO_IDX,
        "class_weights":    CLASS_WEIGHTS,
        "input_size":       224,
        "phase1_epochs":    phase1_epochs,
        "phase2_epochs":    phase2_epochs,
        "batch_size":       batch_size,
        "metrics": {
            "overall_accuracy_pct":                  round(overall_acc, 2),
            "roc_auc_ovr":                           round(roc_auc, 4),
            "high_stakes_false_negative_rate_pct":   fn_rate,
            "subdataset_accuracy":                   subdataset_metrics,
            "classification_report":                 cls_report_dict,
        },
        "real_photo_retest":    retest_results or [],
        "training_time_seconds": round(time.time() - start_total, 2),
    }

    meta_file = out_path / "metadata_v4.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    report_file = reports_path / "evaluation_report_v4.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n  [*] Metadata -> {meta_file}")
    print(f"  [*] Report   -> {report_file}")
    print(f"\n  Total wall-clock time: {(time.time()-start_total)/60:.1f} min")
    print("=" * 80)


# -----------------------------------------------------------------------------
# 7. ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EfficientNetB0 v4 with random-scale crop augmentation")
    parser.add_argument("--data_dir",       type=str,   default=None,  help="Path to base dataset root")
    parser.add_argument("--manifest",       type=str,   default=None,  help="Path to manifest CSV")
    parser.add_argument("--output_dir",     type=str,   default=None,  help="Path to save weights")
    parser.add_argument("--batch_size",     type=int,   default=64,    help="Training batch size (default 64)")
    parser.add_argument("--phase1_epochs",  type=int,   default=3,     help="Phase 1 frozen-head epochs (default 3)")
    parser.add_argument("--phase2_epochs",  type=int,   default=0,     help="Phase 2 fine-tune epochs (default 0)")
    parser.add_argument("--sample_limit",   type=int,   default=None,  help="Optional mini-subset limit")
    parser.add_argument("--no_timing_gate", action="store_true",       help="Disable auto-abort if epoch 1 is slow")
    args = parser.parse_args()

    train_v4(
        manifest_path=args.manifest,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        phase1_epochs=args.phase1_epochs,
        phase2_epochs=args.phase2_epochs,
        sample_limit=args.sample_limit,
        abort_after_epoch1_if_slow=not args.no_timing_gate,
    )
