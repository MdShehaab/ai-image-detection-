"""
Benchmarked Smoke Test for 3-Class EfficientNetB0 Image Authenticity Classifier.
Enforces explicit device placement and @tf.function compiled GPU training steps.
"""

import os
import sys
import time
import random
import csv
import threading
from pathlib import Path
import numpy as np
import pandas as pd
import cv2
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(r"c:\Users\sheha\OneDrive\Desktop\new project").resolve()
MANIFEST_PATH = PROJECT_ROOT / "datasets" / "manifest_combined.csv"
WEIGHTS_DIR = PROJECT_ROOT / "backend" / "models" / "image_detector" / "weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
SMOKE_MODEL_PATH = WEIGHTS_DIR / "smoke_test.keras"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_TO_IDX = {"ai_generated": 0, "ai_modified": 1, "real": 2}
IDX_TO_CLASS = {v: k for k, v in CLASS_TO_IDX.items()}
CLASS_WEIGHTS_LIST = [1.45, 1.52, 1.00]
CLASS_WEIGHTS = {0: 1.45, 1: 1.52, 2: 1.00}

_thread_local = threading.local()

def get_face_cascade():
    if not hasattr(_thread_local, "cascade"):
        _thread_local.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    return _thread_local.cascade

def get_var_device(var):
    """Retrieve underlying device string across TF 2.x and Keras 3."""
    if hasattr(var, "device"): return var.device
    if hasattr(var, "value") and hasattr(var.value, "device"): return var.value.device
    if hasattr(var, "handle") and hasattr(var.handle, "device"): return var.handle.device
    return "unknown"

def resolve_image_path(rel_path: str) -> Path:
    p = PROJECT_ROOT / "datasets" / rel_path
    if p.exists(): return p
    p2 = Path(r"C:\Users\sheha\OneDrive\Desktop\AI-Powered Visual Deepfake Detection and Analysis System\datasets") / rel_path
    if p2.exists(): return p2
    p3 = Path(r"C:\Users\sheha\OneDrive\Desktop\AI-Powered Visual Deepfake Detection and Analysis System\dataset") / rel_path
    if p3.exists(): return p3
    p4 = PROJECT_ROOT / rel_path
    if p4.exists(): return p4
    return p

def load_and_preprocess_image(
    rel_path: str,
    source_dataset: str,
    is_training: bool = False,
    target_size: tuple = (224, 224)
) -> np.ndarray:
    abs_path = resolve_image_path(rel_path)
    if not abs_path.exists():
        return np.zeros((target_size[0], target_size[1], 3), dtype=np.float32)

    img_bgr = cv2.imread(str(abs_path))
    if img_bgr is None:
        return np.zeros((target_size[0], target_size[1], 3), dtype=np.float32)

    h, w, _ = img_bgr.shape

    if "faceforensics" in source_dataset.lower():
        face_cascade = get_face_cascade()
        scale = 320.0 / max(h, w)
        if scale < 1.0:
            thumb_w = int(w * scale)
            thumb_h = int(h * scale)
            thumb_bgr = cv2.resize(img_bgr, (thumb_w, thumb_h), interpolation=cv2.INTER_NEAREST)
            gray = cv2.cvtColor(thumb_bgr, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))
            inv_scale = 1.0 / scale
            scaled_faces = [[int(x * inv_scale), int(y * inv_scale), int(fw * inv_scale), int(fh * inv_scale)] for x, y, fw, fh in faces]
        else:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            scaled_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))

        if len(scaled_faces) > 0:
            fx, fy, fw, fh = max(scaled_faces, key=lambda b: b[2] * b[3])
            margin_x = int(0.20 * fw)
            margin_y = int(0.20 * fh)
            x1 = max(0, fx - margin_x)
            y1 = max(0, fy - margin_y)
            x2 = min(w, fx + fw + margin_x)
            y2 = min(h, fy + fh + margin_y)
            cropped = img_bgr[y1:y2, x1:x2]
        else:
            min_dim = min(h, w)
            sy = (h - min_dim) // 2
            sx = (w - min_dim) // 2
            cropped = img_bgr[sy:sy + min_dim, sx:sx + min_dim]

        resized = cv2.resize(cropped, target_size, interpolation=cv2.INTER_LINEAR)
    else:
        resized = cv2.resize(img_bgr, target_size, interpolation=cv2.INTER_LINEAR)

    if is_training:
        if random.random() > 0.5:
            resized = cv2.flip(resized, 1)
        angle = random.uniform(-10, 10)
        M = cv2.getRotationMatrix2D((target_size[0] / 2, target_size[1] / 2), angle, 1.0)
        resized = cv2.warpAffine(resized, M, target_size, borderMode=cv2.BORDER_REFLECT)
        quality = random.randint(70, 95)
        _, enc = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        resized = cv2.imdecode(enc, 1)
        alpha, beta = random.uniform(0.9, 1.1), random.uniform(-15, 15)
        resized = cv2.convertScaleAbs(resized, alpha=alpha, beta=beta)

    img_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    return img_rgb.astype(np.float32)

def create_tf_data_pipeline(df: pd.DataFrame, batch_size: int = 32, is_training: bool = False) -> tf.data.Dataset:
    image_paths = df["image_path"].values.astype(str)
    source_datasets = df["source_dataset"].values.astype(str)
    labels = df["class"].map(CLASS_TO_IDX).values.astype(np.int32)

    ds = tf.data.Dataset.from_tensor_slices((image_paths, source_datasets, labels))
    if is_training:
        ds = ds.shuffle(buffer_size=min(len(df), 2048), reshuffle_each_iteration=True)

    def _py_loader(p_bytes, s_bytes, is_train_bool):
        p_str = p_bytes.numpy().decode("utf-8")
        s_str = s_bytes.numpy().decode("utf-8")
        return load_and_preprocess_image(p_str, s_str, is_training=bool(is_train_bool))

    def _map_fn(p, s, l):
        img = tf.py_function(func=_py_loader, inp=[p, s, is_training], Tout=tf.float32)
        img.set_shape([224, 224, 3])
        l.set_shape([])
        return img, l

    ds = ds.map(_map_fn, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size, drop_remainder=False)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds

def run_benchmarked_smoke_test():
    start_total_time = time.time()
    print("=" * 80)
    print(" AI-POWERED IMAGE AUTHENTICITY CLASSIFIER - HARDWARE & DEVICE AUDIT")
    print("=" * 80)
    
    gpus = tf.config.list_physical_devices('GPU')
    active_device = "/GPU:0" if gpus else "/CPU:0"
    print(f"[*] Physical GPU Devices   : {gpus}")
    print(f"[*] Target Compute Device  : {active_device}")

    # Explicit device context for model construction
    with tf.device(active_device):
        base_model = tf.keras.applications.EfficientNetB0(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
        x = tf.keras.layers.GlobalAveragePooling2D(name="avg_pool")(base_model.output)
        x = tf.keras.layers.Dense(256, activation="relu", name="dense_256")(x)
        x = tf.keras.layers.Dropout(0.3, name="dropout_0.3")(x)
        outputs = tf.keras.layers.Dense(3, activation="softmax", name="predictions")(x)
        model = tf.keras.Model(inputs=base_model.input, outputs=outputs, name="EfficientNetB0_Authenticity")

        optimizer_p1 = tf.keras.optimizers.Adam(1e-3)
        loss_fn = tf.keras.losses.SparseCategoricalCrossentropy()
        class_weights_t = tf.constant(CLASS_WEIGHTS_LIST, dtype=tf.float32)

    # 1. Device Placement Verification
    var0 = model.trainable_variables[0]
    var0_device = get_var_device(var0)
    print("\n" + "-" * 80)
    print(f"[*] DEVICE PLACEMENT AUDIT:")
    print(f"    - Variable 0 Name      : {var0.name}")
    print(f"    - Variable 0 Device    : {var0_device}")
    print(f"    - Total Model Layers   : {len(model.layers)}")
    print(f"    - Trainable Variables  : {len(model.trainable_variables)}")
    print("-" * 80 + "\n")

    # Load dataset sample
    full_df = pd.read_csv(MANIFEST_PATH)
    train_samples, val_samples, test_samples = [], [], []
    for c in ("ai_generated", "ai_modified", "real"):
        train_samples.append(full_df[(full_df["split"] == "train") & (full_df["class"] == c)].sample(n=200, random_state=42))
        val_samples.append(full_df[(full_df["split"] == "validation") & (full_df["class"] == c)].sample(n=50, random_state=42))
        test_samples.append(full_df[(full_df["split"] == "test") & (full_df["class"] == c)].sample(n=50, random_state=42))

    train_df = pd.concat(train_samples).sample(frac=1, random_state=42).reset_index(drop=True)
    val_df = pd.concat(val_samples).sample(frac=1, random_state=42).reset_index(drop=True)
    test_df = pd.concat(test_samples).sample(frac=1, random_state=42).reset_index(drop=True)

    train_ds = create_tf_data_pipeline(train_df, batch_size=32, is_training=True)
    val_ds = create_tf_data_pipeline(val_df, batch_size=32, is_training=False)
    test_ds = create_tf_data_pipeline(test_df, batch_size=32, is_training=False)

    # Define @tf.function compiled GPU training steps
    @tf.function
    def train_step_compiled(images, labels, opt):
        with tf.GradientTape() as tape:
            preds = model(images, training=True)
            loss_raw = loss_fn(labels, preds)
            weights = tf.gather(class_weights_t, labels)
            loss = tf.reduce_mean(loss_raw * weights)
        grads = tape.gradient(loss, model.trainable_variables)
        opt.apply_gradients(zip(grads, model.trainable_variables))
        acc = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(preds, axis=1, output_type=tf.int32), labels), tf.float32))
        return loss, acc

    # Warmup graph trace for Phase 1
    base_model.trainable = False
    optimizer_p1.build(model.trainable_variables)
    dummy_x = tf.zeros((32, 224, 224, 3), dtype=tf.float32)
    dummy_y = tf.zeros((32,), dtype=tf.int32)
    _ = train_step_compiled(dummy_x, dummy_y, optimizer_p1)
    print("[*] Phase 1 JIT Graph Trace compiled successfully.\n")


    # ==========================================================================
    # PHASE 1: COMPILED STEP TRAINING (1 Epoch)
    # ==========================================================================
    print("=" * 80)
    print(" [*] PHASE 1: TRAINING HEAD (1 Epoch) WITH COMPILED @tf.function")
    print("=" * 80)

    data_load_times_p1 = []
    model_compute_times_p1 = []
    
    ds_iter = iter(train_ds)
    batch_count = int(np.ceil(len(train_df) / 32))

    for b_idx in range(batch_count):
        t_d0 = time.time()
        X_b, y_b = next(ds_iter)
        t_data = time.time() - t_d0
        data_load_times_p1.append(t_data)

        t_c0 = time.time()
        loss, acc = train_step_compiled(X_b, y_b, optimizer_p1)
        t_comp = time.time() - t_c0
        model_compute_times_p1.append(t_comp)

        print(f"  Phase 1 Batch [{b_idx+1}/{batch_count}] - Data: {t_data*1000:5.1f}ms | Compute: {t_comp*1000:5.1f}ms | Loss: {float(loss):.4f} - Acc: {float(acc)*100:.1f}%")

    # ==========================================================================
    # PHASE 2: COMPILED FINE-TUNING TOP 30 (1 Epoch)
    # ==========================================================================
    print("\n" + "=" * 80)
    print(" [*] PHASE 2: FINE-TUNING TOP 30 LAYERS (1 Epoch) WITH COMPILED @tf.function")
    print("=" * 80)
    base_model.trainable = True
    for layer in base_model.layers[:-30]: layer.trainable = False
    for layer in base_model.layers[-30:]: layer.trainable = True

    optimizer_p2 = tf.keras.optimizers.Adam(1e-5)
    optimizer_p2.build(model.trainable_variables)
    _ = train_step_compiled(dummy_x, dummy_y, optimizer_p2)
    print("[*] Phase 2 JIT Graph Trace compiled successfully with unfrozen layers.\n")


    data_load_times_p2 = []
    model_compute_times_p2 = []
    ds_iter2 = iter(train_ds)

    for b_idx in range(batch_count):
        t_d0 = time.time()
        X_b, y_b = next(ds_iter2)
        t_data = time.time() - t_d0
        data_load_times_p2.append(t_data)

        t_c0 = time.time()
        loss, acc = train_step_compiled(X_b, y_b, optimizer_p2)
        t_comp = time.time() - t_c0
        model_compute_times_p2.append(t_comp)

        print(f"  Phase 2 Batch [{b_idx+1}/{batch_count}] - Data: {t_data*1000:5.1f}ms | Compute: {t_comp*1000:5.1f}ms | Loss: {float(loss):.4f} - Acc: {float(acc)*100:.1f}%")

    model.save(SMOKE_MODEL_PATH)
    print(f"\n[*] Saved smoke test weights to: {SMOKE_MODEL_PATH}")

    # ==========================================================================
    # EVALUATION ON TEST SET
    # ==========================================================================
    print("\n" + "=" * 80)
    print("                    EVALUATION ON TEST SPLIT (150 Samples)")
    print("=" * 80)
    y_true_all, y_pred_probs_all = [], []
    for X_b, y_b in test_ds:
        probs = model(X_b, training=False)
        y_pred_probs_all.append(probs.numpy())
        y_true_all.append(y_b.numpy())

    y_true = np.concatenate(y_true_all)
    y_probs = np.concatenate(y_pred_probs_all)
    y_preds = np.argmax(y_probs, axis=1)

    overall_acc = np.mean(y_preds == y_true) * 100
    target_names = [IDX_TO_CLASS[i] for i in range(3)]
    
    print(f"[*] Overall Test Accuracy : {overall_acc:.2f}%\n")
    print(classification_report(y_true, y_preds, target_names=target_names, digits=4, zero_division=0))

    cm = confusion_matrix(y_true, y_preds, labels=[0, 1, 2])
    print("--- 3x3 Confusion Matrix ---")
    header_cm = f"{'True \\ Pred':<16}" + "".join([f"{c:<16}" for c in target_names])
    print(header_cm)
    for idx_r, row in enumerate(cm):
        r_str = f"{target_names[idx_r]:<16}" + "".join([f"{val:<16}" for val in row])
        print(r_str)

    y_true_onehot = np.eye(3)[y_true]
    roc_auc = roc_auc_score(y_true_onehot, y_probs, multi_class='ovr')
    print(f"\n[*] Multi-Class One-vs-Rest ROC-AUC: {roc_auc:.4f}")

    avg_data_p1_ms = np.mean(data_load_times_p1) * 1000
    avg_comp_p1_ms = np.mean(model_compute_times_p1) * 1000
    avg_total_p1_ms = avg_data_p1_ms + avg_comp_p1_ms

    avg_data_p2_ms = np.mean(data_load_times_p2) * 1000
    avg_comp_p2_ms = np.mean(model_compute_times_p2) * 1000
    avg_total_p2_ms = avg_data_p2_ms + avg_comp_p2_ms

    print("\n" + "=" * 80)
    print("                FINAL BENCHMARK & HARDWARE SUMMARY")
    print("=" * 80)
    print(f"[*] Model Variable Device : {var0_device}")
    print(f"[*] Phase 1 Per-Sample    : {avg_total_p1_ms/32:.2f} ms/sample (Compute: {avg_comp_p1_ms/32:.2f} ms | Data: {avg_data_p1_ms/32:.2f} ms)")
    print(f"[*] Phase 2 Per-Sample    : {avg_total_p2_ms/32:.2f} ms/sample (Compute: {avg_comp_p2_ms/32:.2f} ms | Data: {avg_data_p2_ms/32:.2f} ms)")
    print(f"[*] Total Wall-Clock Time : {time.time() - start_total_time:.2f}s")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_benchmarked_smoke_test()
