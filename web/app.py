"""
Flask Web Application - Deteksi Kematangan Daun Ketapang
Cara pakai: python web/app.py
"""

import os, sys, json, uuid, base64, io

# Fix encoding for Windows console (emojis)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow import keras
import cv2

# ============================================================
# KONFIGURASI
# ============================================================
IMG_SIZE = 224
MIN_CONFIDENCE = 0.50  # Minimum confidence to accept a prediction
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BASE_DIR, 'saved_model')
MODEL_PATH = os.path.join(SAVE_DIR, 'best_model.keras')
CLASS_MAP_PATH = os.path.join(SAVE_DIR, 'class_names.json')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}

# Class info
CLASS_INFO = {
    'daun muda': {
        'label': 'Daun Muda',
        'color': '#4CAF50',
        'emoji': '🟢',
        'description': 'Daun dalam fase pertumbuhan awal dengan warna hijau muda segar. Tekstur lunak dan halus, biasanya ditemukan di ujung ranting.',
        'characteristics': ['Warna hijau muda segar', 'Tekstur lunak dan halus', 'Ukuran lebih kecil', 'Terletak di ujung ranting']
    },
    'daun menguning': {
        'label': 'Daun Menguning (Sedang)',
        'color': '#FF9800',
        'emoji': '🟤',
        'description': 'Daun yang mulai memasuki fase dewasa/matang dengan warna yang mulai menguning. Tekstur kaku dan optimal dalam fotosintesis.',
        'characteristics': ['Warna hijau tua/kekuningan', 'Tekstur kaku dan mengkilap', 'Ukuran maksimal', 'Fotosintesis optimal']
    },
    'daun tua': {
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

def cleanup_uploads():
    """Bersihkan folder uploads saat server start"""
    count = 0
    for f in os.listdir(UPLOAD_FOLDER):
        fpath = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(fpath):
            try:
                os.remove(fpath)
                count += 1
            except: pass
    if count > 0:
        print(f"🧹 Membersihkan {count} file lama dari uploads")

# Load model
model = None
class_names = ['daun muda', 'daun menguning', 'daun tua']

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


def detect_leaf_bbox(image_path):
    """Mendeteksi kontur daun Ketapang dan mengembalikan bounding box ternormalisasi (0-1)"""
    try:
        img = cv2.imread(image_path)
        if img is None: return None
        
        h_img, w_img, _ = img.shape
        total_area = h_img * w_img
        
        # Convert to HSV untuk segmentasi warna
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # --- Exclude warna kulit (skin tone) --- dipersempit agar daun tua cokelat tidak ikut terbuang
        lower_skin = np.array([5, 30, 100])
        upper_skin = np.array([17, 140, 255])
        mask_skin = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Range warna hijau (daun muda/sedang)
        lower_green = np.array([25, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        # Range warna cokelat/oranye (daun tua ketapang - diperlebar signifikan)
        lower_brown = np.array([5, 50, 20])
        upper_brown = np.array([25, 255, 220])
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
        
        # Range merah gelap (daun sangat tua/kering)
        lower_dred = np.array([0, 50, 20])
        upper_dred = np.array([8, 255, 200])
        mask_dred = cv2.inRange(hsv, lower_dred, upper_dred)
        
        # Range kuning-cokelat muda (daun tua transisi)
        lower_yellow = np.array([20, 40, 40])
        upper_yellow = np.array([30, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Gabungkan warna daun, lalu exclude kulit
        mask_leaf = cv2.bitwise_or(mask_green, cv2.bitwise_or(mask_brown, cv2.bitwise_or(mask_dred, mask_yellow)))
        mask = cv2.bitwise_and(mask_leaf, cv2.bitwise_not(mask_skin))
        
        # Cleaning noise (lebih agresif)
        kernel = np.ones((7,7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Filter kontur berdasarkan bentuk daun
        best = None
        best_score = 0
        
        for c in contours:
            area = cv2.contourArea(c)
            area_ratio = area / total_area
            
            # Skip terlalu kecil (<1% frame) atau terlalu besar (>70% frame)
            if area_ratio < 0.01 or area_ratio > 0.70:
                continue
            
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = max(w, h) / (min(w, h) + 1e-6)
            
            # Daun ketapang punya aspect ratio ~1.2 - 3.0 (oval/lonjong)
            if aspect_ratio > 3.5: # Lebih ketat, daun ketapang ga sepanjang itu
                continue
            
            # Hitung solidity (area kontur / area convex hull) - daun ~0.6-0.95
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0:
                continue
            solidity = area / hull_area
            
            if solidity < 0.55: # Dinaikin dari 0.4 biar objek acak/kain kusut ga masuk
                continue
            
            # Score: prefer area sedang dan solidity tinggi
            score = area_ratio * solidity
            if score > best_score:
                best_score = score
                best = (x, y, w, h)
        
        if best:
            x, y, w, h = best
            # Tambah sedikit padding (5%)
            pad_x = int(w * 0.05)
            pad_y = int(h * 0.05)
            x = max(0, x - pad_x)
            y = max(0, y - pad_y)
            w = min(w_img - x, w + 2 * pad_x)
            h = min(h_img - y, h + 2 * pad_y)
            
            return {
                'x': float(x / w_img),
                'y': float(y / h_img),
                'w': float(w / w_img),
                'h': float(h / h_img)
            }
    except Exception as e:
        print(f"⚠️ Error deteksi bbox: {e}")
    return None

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
        is_camera = False
        
        # Check if request is JSON (base64 image from camera)
        if request.is_json:
            is_camera = True
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
            if is_camera:
                try: os.remove(filepath)
                except: pass
            return jsonify({
                'error': 'Model belum di-training! Jalankan: python model/train.py',
                'demo_mode': True
            }), 503

        # Get class info
        info = CLASS_INFO.get(predicted_class, {})
        
        # Detect BBox
        bbox = detect_leaf_bbox(filepath)
        
        # VALIDASI KETAT: Jika opencv tidak menemukan kontur daun, tolak prediksi
        # Ini mencegah model menebak asal saat diarahkan ke tembok/kasur/kulit
        if bbox is None:
            if is_camera:
                try: os.remove(filepath)
                except: pass
            return jsonify({'success': False, 'error': 'Tidak ada daun terdeteksi'})

        # Check minimum confidence — if too low, return uncertain result
        if confidence < MIN_CONFIDENCE:
            if is_camera:
                try: os.remove(filepath)
                except: pass
            return jsonify({
                'success': True,
                'prediction': {
                    'class': 'unknown',
                    'label': 'Tidak Yakin',
                    'confidence': confidence,
                    'confidence_percent': f"{confidence * 100:.2f}%",
                    'color': '#f59e0b',
                    'emoji': '❓',
                    'description': f'Model tidak cukup yakin ({confidence*100:.1f}%). Coba perbaiki pencahayaan, sudut pengambilan, atau pastikan daun terlihat jelas. Jika masalah berlanjut, dataset perlu ditambah dan model di-retrain.',
                    'characteristics': ['Confidence terlalu rendah', 'Coba sudut lain', 'Perbaiki pencahayaan', 'Dekatkan daun ke kamera'],
                    'bbox': bbox
                },
                'probabilities': probabilities,
                'image_url': None if is_camera else f'/static/uploads/{filename}'
            })

        # Auto-cleanup: hapus file dari live camera setelah prediksi
        if is_camera:
            try:
                os.remove(filepath)
            except Exception:
                pass

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
                'characteristics': info.get('characteristics', []),
                'bbox': bbox
            },
            'probabilities': probabilities,
            'image_url': None if is_camera else f'/static/uploads/{filename}'
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
    cleanup_uploads()
    print("\n" + "=" * 50)
    print("🌿 Deteksi Kematangan Daun Ketapang")
    print("   Server: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
