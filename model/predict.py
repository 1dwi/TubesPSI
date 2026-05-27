"""
Predict Script - Deteksi Kematangan Daun Ketapang
Prediksi single image dari command line.

Cara pakai:
    python model/predict.py path/to/image.jpg
"""

import os, sys, json, numpy as np

# Fix encoding for Windows console (emojis)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import tensorflow as tf
from tensorflow import keras
from PIL import Image

IMG_SIZE = 224
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BASE_DIR, 'saved_model')
MODEL_PATH = os.path.join(SAVE_DIR, 'best_model.keras')
CLASS_MAP_PATH = os.path.join(SAVE_DIR, 'class_names.json')

LABEL_INFO = {
    'daun muda': {'emoji': '🟢', 'desc': 'Daun muda - Hijau muda segar, tekstur lunak'},
    'daun menguning': {'emoji': '🟤', 'desc': 'Daun menguning - Hijau tua/kekuningan, tekstur kaku'},
    'daun tua': {'emoji': '🔴', 'desc': 'Daun tua - Kuning/merah/oranye, kering rapuh'}
}

def predict_image(image_path):
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model tidak ditemukan: {MODEL_PATH}")
        sys.exit(1)
    if not os.path.exists(image_path):
        print(f"❌ Gambar tidak ditemukan: {image_path}")
        sys.exit(1)

    # Load config
    if os.path.exists(CLASS_MAP_PATH):
        with open(CLASS_MAP_PATH, 'r') as f:
            class_names = json.load(f)['class_names']
    else:
        class_names = ['muda', 'sedang', 'tua']

    # Load model
    print("📂 Loading model...")
    model = keras.models.load_model(MODEL_PATH)

    # Preprocess image
    img = Image.open(image_path).convert('RGB').resize((IMG_SIZE, IMG_SIZE))
    img_array = np.expand_dims(np.array(img), axis=0).astype('float32')

    # Predict
    predictions = model.predict(img_array, verbose=0)[0]
    predicted_idx = np.argmax(predictions)
    predicted_class = class_names[predicted_idx]
    confidence = predictions[predicted_idx]

    # Display results
    info = LABEL_INFO.get(predicted_class, {'emoji': '❓', 'desc': '-'})
    print(f"\n{'='*50}")
    print(f"🌿 HASIL PREDIKSI")
    print(f"{'='*50}")
    print(f"   Gambar : {os.path.basename(image_path)}")
    print(f"   Kelas  : {info['emoji']} {predicted_class.upper()}")
    print(f"   Confidence: {confidence:.4f} ({confidence*100:.2f}%)")
    print(f"   Deskripsi : {info['desc']}")
    print(f"\n   Probabilitas semua kelas:")
    for i, cls in enumerate(class_names):
        bar = '█' * int(predictions[i] * 30)
        print(f"     {cls:8s}: {predictions[i]:.4f} {bar}")
    print(f"{'='*50}")

    return predicted_class, confidence, {cls: float(predictions[i]) for i, cls in enumerate(class_names)}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python model/predict.py <image_path>")
        sys.exit(1)
    predict_image(sys.argv[1])
