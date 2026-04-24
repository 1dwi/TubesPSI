"""
Evaluation Script - Deteksi Kematangan Daun Ketapang
Cara pakai: python model/evaluate.py
"""

import os, sys, json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
import seaborn as sns

IMG_SIZE = 224
BATCH_SIZE = 32
RANDOM_SEED = 42
VALIDATION_SPLIT = 0.2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
SAVE_DIR = os.path.join(BASE_DIR, 'saved_model')
MODEL_PATH = os.path.join(SAVE_DIR, 'best_model.keras')
CLASS_MAP_PATH = os.path.join(SAVE_DIR, 'class_names.json')
REPORT_DIR = os.path.join(SAVE_DIR, 'evaluation')

def main():
    print("=" * 60)
    print("🌿 EVALUASI: Deteksi Kematangan Daun Ketapang")
    print("=" * 60)

    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model tidak ditemukan: {MODEL_PATH}")
        print("   Jalankan training dulu: python model/train.py")
        sys.exit(1)

    model = keras.models.load_model(MODEL_PATH)

    if os.path.exists(CLASS_MAP_PATH):
        with open(CLASS_MAP_PATH, 'r') as f:
            config = json.load(f)
        class_names = config['class_names']
    else:
        class_names = ['muda', 'sedang', 'tua']

    val_ds = keras.utils.image_dataset_from_directory(
        DATASET_DIR, validation_split=VALIDATION_SPLIT, subset='validation',
        seed=RANDOM_SEED, image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE, label_mode='categorical', class_names=class_names
    )

    os.makedirs(REPORT_DIR, exist_ok=True)

    y_true, y_pred, y_prob = [], [], []
    for images, labels in val_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(np.argmax(labels.numpy(), axis=1))
        y_pred.extend(np.argmax(preds, axis=1))
        y_prob.extend(preds)

    y_true, y_pred, y_prob = np.array(y_true), np.array(y_pred), np.array(y_prob)

    report = classification_report(y_true, y_pred, target_names=class_names, digits=4)
    accuracy = accuracy_score(y_true, y_pred)
    print("\n" + report)
    print(f"Overall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

    with open(os.path.join(REPORT_DIR, 'evaluation_report.txt'), 'w') as f:
        f.write("EVALUATION REPORT - Daun Ketapang\n" + "="*60 + "\n" + report)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens',
                xticklabels=class_names, yticklabels=class_names,
                linewidths=0.5, square=True, annot_kws={"size": 16})
    plt.title('Confusion Matrix', fontsize=16, fontweight='bold')
    plt.xlabel('Predicted'); plt.ylabel('Actual')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, 'confusion_matrix.png'), dpi=150)
    plt.close()

    # Per-class accuracy
    colors = ['#4CAF50', '#FF9800', '#F44336']
    per_class_acc = cm.diagonal() / cm.sum(axis=1)
    plt.figure(figsize=(8, 5))
    bars = plt.bar(class_names, per_class_acc, color=colors)
    for bar, acc in zip(bars, per_class_acc):
        plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                f'{acc:.2%}', ha='center', fontsize=13, fontweight='bold')
    plt.title('Akurasi Per Kelas', fontsize=16, fontweight='bold')
    plt.ylabel('Accuracy'); plt.ylim(0, 1.15); plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, 'per_class_accuracy.png'), dpi=150)
    plt.close()

    print(f"\n✅ Reports saved to: {REPORT_DIR}")

if __name__ == '__main__':
    main()
