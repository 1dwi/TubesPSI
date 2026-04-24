"""
Flask Web Application - Deteksi Kematangan Daun Ketapang
Cara pakai: python web/app.py
"""

import os, sys, json, uuid, base64, io
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow import keras

# ============================================================
# KONFIGURASI
# ============================================================
IMG_SIZE = 224
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BASE_DIR, 'saved_model')
MODEL_PATH = os.path.join(SAVE_DIR, 'best_model.keras')
CLASS_MAP_PATH = os.path.join(SAVE_DIR, 'class_names.json')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}

# Class info
CLASS_INFO = {
    'muda': {
        'label': 'Daun Muda',
        'color': '#4CAF50',
        'emoji': '🟢',
        'description': 'Daun dalam fase pertumbuhan awal dengan warna hijau muda segar. Tekstur lunak dan halus, biasanya ditemukan di ujung ranting.',
        'characteristics': ['Warna hijau muda segar', 'Tekstur lunak dan halus', 'Ukuran lebih kecil', 'Terletak di ujung ranting']
    },
    'sedang': {
        'label': 'Daun Sedang (Dewasa)',
        'color': '#FF9800',
        'emoji': '🟤',
        'description': 'Daun yang sudah matang sempurna dengan warna hijau tua. Tekstur kaku dan mengkilap, optimal dalam fotosintesis.',
        'characteristics': ['Warna hijau tua', 'Tekstur kaku dan mengkilap', 'Ukuran maksimal', 'Fotosintesis optimal']
    },
    'tua': {
        'label': 'Daun Tua',
        'color': '#F44336',
        'emoji': '🔴',
        'description': 'Daun yang akan segera gugur dengan perubahan warna dari kuning ke merah/oranye. Tekstur kering dan rapuh.',
        'characteristics': ['Warna kuning/merah/oranye', 'Tekstur kering dan rapuh', 'Klorofil berkurang', 'Akan segera gugur']
    }
}

# ============================================================
# APP SETUP
# ============================================================
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load model
model = None
class_names = ['muda', 'sedang', 'tua']

def load_model():
    global model, class_names
    if os.path.exists(MODEL_PATH):
        print("📂 Loading model...")
        model = keras.models.load_model(MODEL_PATH)
        if os.path.exists(CLASS_MAP_PATH):
            with open(CLASS_MAP_PATH, 'r') as f:
                class_names = json.load(f)['class_names']
        print(f"✅ Model loaded! Classes: {class_names}")
    else:
        print(f"⚠️  Model belum ada: {MODEL_PATH}")
        print("   Jalankan training dulu: python model/train.py")
        print("   Web app akan berjalan dalam mode DEMO (random prediction)")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    img = Image.open(image_path).convert('RGB').resize((IMG_SIZE, IMG_SIZE))
    return np.expand_dims(np.array(img), axis=0).astype('float32')

# ============================================================
# ROUTES
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Check if request is JSON (base64 image from camera)
        if request.is_json:
            data = request.json
            if 'image' not in data:
                return jsonify({'error': 'Tidak ada data gambar'}), 400
                
            # Decode base64
            img_data = data['image']
            if "base64," in img_data:
                img_data = img_data.split("base64,")[1]
            
            image_bytes = base64.b64decode(img_data)
            image = Image.open(io.BytesIO(image_bytes))
            image.save(filepath)
            
        # Otherwise assume it's a file upload
        else:
            if 'file' not in request.files:
                return jsonify({'error': 'Tidak ada file yang diupload'}), 400
        
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Tidak ada file yang dipilih'}), 400
        
            if not allowed_file(file.filename):
                return jsonify({'error': f'Format file tidak didukung. Gunakan: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
            # Save uploaded file
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

        if model is not None:
            # Real prediction
            img_array = preprocess_image(filepath)
            predictions = model.predict(img_array, verbose=0)[0]
            predicted_idx = int(np.argmax(predictions))
            predicted_class = class_names[predicted_idx]
            confidence = float(predictions[predicted_idx])
            probabilities = {cls: float(predictions[i]) for i, cls in enumerate(class_names)}
        else:
            # Demo mode (no model loaded)
            predicted_class = 'muda'
            confidence = 0.0
            probabilities = {cls: 0.0 for cls in class_names}
            return jsonify({
                'error': 'Model belum di-training! Jalankan: python model/train.py',
                'demo_mode': True
            }), 503

        # Get class info
        info = CLASS_INFO.get(predicted_class, {})

        return jsonify({
            'success': True,
            'prediction': {
                'class': predicted_class,
                'label': info.get('label', predicted_class),
                'confidence': confidence,
                'confidence_percent': f"{confidence * 100:.2f}%",
                'color': info.get('color', '#666'),
                'emoji': info.get('emoji', ''),
                'description': info.get('description', ''),
                'characteristics': info.get('characteristics', [])
            },
            'probabilities': probabilities,
            'image_url': f'/static/uploads/{filename}'
        })

    except Exception as e:
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'classes': class_names
    })

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    load_model()
    print("\n" + "=" * 50)
    print("🌿 Deteksi Kematangan Daun Ketapang")
    print("   Server: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
