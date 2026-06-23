"""
Training Script - Skenario B
Menggunakan MobileNetV2 (Partial Fine-Tuning)

Cara pakai:
    python model/train.py

Dataset harus diletakkan di folder dataset/ dengan struktur:
    dataset/
    ├── muda/       # Gambar daun muda (hijau muda)
    ├── sedang/     # Gambar daun sedang/dewasa (hijau tua)
    └── tua/        # Gambar daun tua (kuning/merah/coklat)

Referensi:
    - MobileNetV2: Sandler et al., 2018. "MobileNetV2: Inverted Residuals and
      Linear Bottlenecks". CVPR 2018. https://arxiv.org/abs/1801.04381
    - Transfer Learning Guide: https://www.tensorflow.org/tutorials/images/transfer_learning
    - Fine-tuning Strategy: https://keras.io/guides/transfer_learning/
    - Data Augmentation: https://www.tensorflow.org/tutorials/images/data_augmentation
"""


import os
import sys
import json

# Fix encoding for Windows console (emojis)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ModelCheckpoint,
    ReduceLROnPlateau
)
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

# ============================================================
# KONFIGURASI
# ============================================================
IMG_SIZE = 224                          # Input size MobileNetV2
BATCH_SIZE = 32
EPOCHS_FROZEN = 20                      # Skenario B: 20 Epoch
EPOCHS_FINETUNE = 30                    # Skenario B: 30 Epoch
LEARNING_RATE_FROZEN = 1e-3
LEARNING_RATE_FINETUNE = 1e-4           # Skenario B: LR 1e-4
VALIDATION_SPLIT = 0.2
RANDOM_SEED = 42

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
SAVE_DIR = os.path.join(BASE_DIR, 'saved_model', 'skenario_B')
HISTORY_DIR = os.path.join(SAVE_DIR, 'plots')

# Class names - auto-detect dari folder dataset yang berisi gambar
ALL_CLASS_NAMES = ['daun muda', 'daun menguning', 'daun tua']


def detect_classes():
    """Auto-detect kelas yang memiliki gambar di folder dataset."""
    available = []
    for cls in ALL_CLASS_NAMES:
        cls_path = os.path.join(DATASET_DIR, cls)
        if os.path.exists(cls_path):
            n_images = len([f for f in os.listdir(cls_path)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))])
            if n_images > 0:
                available.append(cls)
    return available


def create_datasets(class_names):
    """Load dan split dataset menjadi train dan validation."""
    print("\n📂 Loading dataset...")
    
    # Cek dan tampilkan info dataset
    for cls in class_names:
        cls_path = os.path.join(DATASET_DIR, cls)
        if not os.path.exists(cls_path):
            print(f"❌ Folder {cls_path} tidak ditemukan!")
            sys.exit(1)
        n_images = len([f for f in os.listdir(cls_path) 
                       if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))])
        print(f"   📁 {cls}: {n_images} gambar")
        if n_images == 0:
            print(f"   ⚠️  Folder '{cls}' kosong! Tambahkan gambar terlebih dahulu.")
            sys.exit(1)
    
    # Load training dataset
    train_ds = keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=VALIDATION_SPLIT,
        subset='training',
        seed=RANDOM_SEED,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        label_mode='categorical',
        class_names=class_names
    )
    
    # Load validation dataset
    val_ds = keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=VALIDATION_SPLIT,
        subset='validation',
        seed=RANDOM_SEED,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        label_mode='categorical',
        class_names=class_names
    )
    
    print(f"\n✅ Dataset loaded!")
    print(f"   Train batches: {len(train_ds)}")
    print(f"   Validation batches: {len(val_ds)}")
    
    return train_ds, val_ds


def build_model(num_classes):
    """Bangun model MobileNetV2 dengan custom classification head."""
    print("\n🏗️  Building model...")
    
    # Data augmentation layer
    data_augmentation = keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.3),
        layers.RandomZoom(0.2),
        layers.RandomBrightness(0.2),
        layers.RandomContrast(0.2),
    ], name='data_augmentation')
    
    # Base model (MobileNetV2 pretrained on ImageNet)
    base_model = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False  # Freeze base model
    
    # Build full model
    inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = data_augmentation(inputs)
    x = keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = keras.Model(inputs, outputs)
    
    print(f"✅ Model built!")
    print(f"   Base model layers: {len(base_model.layers)}")
    print(f"   Total params: {model.count_params():,}")
    
    return model, base_model


def plot_training_history(history, phase_name, save_dir):
    """Plot training & validation accuracy/loss curves."""
    os.makedirs(save_dir, exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Accuracy plot
    ax1.plot(history.history['accuracy'], label='Train Accuracy', linewidth=2)
    ax1.plot(history.history['val_accuracy'], label='Val Accuracy', linewidth=2)
    ax1.set_title(f'Accuracy - {phase_name}', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Loss plot
    ax2.plot(history.history['loss'], label='Train Loss', linewidth=2)
    ax2.plot(history.history['val_loss'], label='Val Loss', linewidth=2)
    ax2.set_title(f'Loss - {phase_name}', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = os.path.join(save_dir, f'{phase_name.lower().replace(" ", "_")}.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   📊 Plot saved: {save_path}")


def plot_confusion_matrix(y_true, y_pred, class_names, save_dir):
    """Plot confusion matrix."""
    os.makedirs(save_dir, exist_ok=True)
    
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Greens',
        xticklabels=class_names,
        yticklabels=class_names,
        linewidths=0.5,
        square=True,
        annot_kws={"size": 14}
    )
    plt.title('Confusion Matrix', fontsize=16, fontweight='bold')
    plt.xlabel('Predicted', fontsize=12)
    plt.ylabel('Actual', fontsize=12)
    plt.tight_layout()
    
    save_path = os.path.join(save_dir, 'confusion_matrix.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   📊 Confusion matrix saved: {save_path}")


def evaluate_model(model, val_ds, class_names, save_dir):
    """Evaluasi model dan generate classification report."""
    print("\n📊 Evaluating model...")
    
    # Get predictions
    y_true = []
    y_pred = []
    
    for images, labels in val_ds:
        predictions = model.predict(images, verbose=0)
        y_true.extend(np.argmax(labels.numpy(), axis=1))
        y_pred.extend(np.argmax(predictions, axis=1))
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Classification report
    report = classification_report(y_true, y_pred, target_names=class_names, digits=4)
    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(report)
    
    # Save report
    report_path = os.path.join(save_dir, 'classification_report.txt')
    with open(report_path, 'w') as f:
        f.write("Classification Report - Deteksi Kematangan Daun Ketapang\n")
        f.write("=" * 60 + "\n")
        f.write(report)
    print(f"   📄 Report saved: {report_path}")
    
    # Plot confusion matrix
    plot_confusion_matrix(y_true, y_pred, class_names, save_dir)
    
    return report


def train():
    """Main training pipeline."""
    print("=" * 60)
    print("🌿 TRAINING: Deteksi Kematangan Daun Ketapang")
    print("   Model: MobileNetV2 (Transfer Learning)")
    print("=" * 60)
    
    # Auto-detect available classes
    CLASS_NAMES = detect_classes()
    if len(CLASS_NAMES) < 2:
        print(f"\n❌ Minimal 2 kelas diperlukan untuk training!")
        print(f"   Kelas ditemukan: {CLASS_NAMES}")
        print(f"   Tambahkan gambar ke folder dataset/ yang kosong.")
        sys.exit(1)
    print(f"\n📋 Kelas terdeteksi: {CLASS_NAMES} ({len(CLASS_NAMES)} kelas)")
    
    # Create output directories
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # Step 1: Load datasets
    train_ds, val_ds = create_datasets(CLASS_NAMES)
    
    # Optimize dataset pipeline
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
    
    # Step 2: Build model
    num_classes = len(CLASS_NAMES)
    print(f"\n   Jumlah kelas: {num_classes}")
    model, base_model = build_model(num_classes)
    
    # Callbacks - checkpoint saves weights only during training, full model saved at end
    checkpoint_path = os.path.join(SAVE_DIR, 'best_model.weights.h5')
    callbacks = [
        EarlyStopping(
            monitor='val_accuracy',
            patience=7,
            restore_best_weights=True,
            verbose=1
        ),
        ModelCheckpoint(
            checkpoint_path,
            monitor='val_accuracy',
            save_best_only=True,
            save_weights_only=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        )
    ]
    
    # ============================================================
    # Phase 1: Train with frozen base model
    # ============================================================
    print("\n" + "=" * 60)
    print("📌 Phase 1: Training dengan base model FROZEN")
    print("=" * 60)
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE_FROZEN),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    history_frozen = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_FROZEN,
        callbacks=callbacks,
        verbose=1
    )
    
    plot_training_history(history_frozen, 'Phase 1 - Frozen', HISTORY_DIR)
    
    # ============================================================
    # Phase 2: Fine-tune top layers of base model
    # ============================================================
    print("\n" + "=" * 60)
    print("📌 Phase 2: Fine-tuning top layers")
    print("=" * 60)
    
    # Unfreeze top 30 layers of base model
    base_model.trainable = True
    fine_tune_at = len(base_model.layers) - 30
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False
    
    trainable_count = sum(1 for layer in base_model.layers if layer.trainable)
    print(f"   Trainable layers in base: {trainable_count}/{len(base_model.layers)}")
    
    # Recompile with lower learning rate
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE_FINETUNE),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    history_finetune = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_FINETUNE,
        callbacks=callbacks,
        verbose=1
    )
    
    plot_training_history(history_finetune, 'Phase 2 - Fine-tune', HISTORY_DIR)
    
    # ============================================================
    # Final Evaluation
    # ============================================================
    evaluate_model(model, val_ds, CLASS_NAMES, HISTORY_DIR)
    
    # Save final model
    final_model_path = os.path.join(SAVE_DIR, 'best_model.keras')
    model.save(final_model_path)
    print(f"\n✅ Model saved: {final_model_path}")
    
    # Save class names mapping
    class_map_path = os.path.join(SAVE_DIR, 'class_names.json')
    with open(class_map_path, 'w') as f:
        json.dump({
            'class_names': CLASS_NAMES,
            'img_size': IMG_SIZE,
            'model_name': 'MobileNetV2'
        }, f, indent=2)
    print(f"✅ Class mapping saved: {class_map_path}")
    
    # Final accuracy
    val_loss, val_acc = model.evaluate(val_ds, verbose=0)
    print(f"\n{'=' * 60}")
    print(f"🎯 FINAL VALIDATION ACCURACY: {val_acc:.4f} ({val_acc*100:.2f}%)")
    print(f"📉 FINAL VALIDATION LOSS: {val_loss:.4f}")
    print(f"{'=' * 60}")
    
    print("\n🌿 Training selesai! Model siap digunakan.")
    print(f"   Jalankan web app: python web/app.py")


if __name__ == '__main__':
    train()
