# 📖 Panduan Lengkap LeafSense AI

Panduan step-by-step untuk setup, training, dan menjalankan aplikasi **deteksi kematangan daun Ketapang** dari nol.

---

## 📌 Daftar Isi

1. [Prasyarat](#-1-prasyarat)
2. [Setup Environment](#-2-setup-environment)
3. [Menyiapkan Dataset](#-3-menyiapkan-dataset)
4. [Training Model](#-4-training-model)
5. [Evaluasi Model](#-5-evaluasi-model)
6. [Menjalankan Web App](#-6-menjalankan-web-app)
7. [Penggunaan Fitur](#-7-penggunaan-fitur)
8. [Troubleshooting](#-8-troubleshooting)

---

## 🔧 1. Prasyarat

Pastikan sudah terinstall di komputer kamu:

| Software | Versi Minimal | Cek Instalasi |
|----------|--------------|---------------|
| **Python** | 3.9+ | `python --version` atau `py --version` |
| **pip** | 21+ | `pip --version` |
| **Git** | (opsional) | `git --version` |
| **Browser** | Chrome/Edge/Firefox terbaru | — |
| **Webcam** | (opsional, untuk live detection) | — |

> ⚠️ **Windows users:** Jika `python` tidak dikenali, coba pakai `py` sebagai gantinya.

---

## 📦 2. Setup Environment

### Langkah 2.1 — Clone / Download Project

```bash
# Clone dari Git (jika ada repo)
git clone <url-repo> "D:\!TUBES PSI DAUN"

# Atau cukup copy folder project ke lokasi yang diinginkan
```

### Langkah 2.2 — Buat Virtual Environment

```bash
# Masuk ke folder project
cd "D:\!TUBES PSI DAUN"

# Buat virtual environment
py -m venv env

# Aktifkan virtual environment
# Windows (PowerShell):
.\env\Scripts\Activate.ps1

# Windows (CMD):
.\env\Scripts\activate.bat
```

> ✅ Kalau berhasil, di terminal akan muncul `(env)` di awal baris.

### Langkah 2.3 — Install Dependencies

```bash
# Pastikan virtual environment sudah aktif (ada tulisan (env))
pip install -r requirements.txt
```

Ini akan menginstall:
- `tensorflow` — Deep learning framework
- `flask` + `flask-cors` — Web server
- `Pillow` — Pemrosesan gambar
- `numpy` — Operasi numerik
- `opencv-python` — Deteksi bounding box
- `matplotlib` + `seaborn` — Plotting
- `scikit-learn` — Evaluasi model

> ⏳ Instalasi TensorFlow bisa memakan waktu 5-15 menit tergantung koneksi internet.

---

## 🖼️ 3. Menyiapkan Dataset

### Struktur Folder

```
dataset/
├── muda/       ← Taruh foto daun MUDA di sini
├── sedang/     ← Taruh foto daun SEDANG/DEWASA di sini
└── tua/        ← Taruh foto daun TUA di sini
```

### Langkah 3.1 — Kumpulkan Foto

| Kelas | Ciri Visual | Jumlah Minimal | Jumlah Ideal |
|-------|-------------|---------------|-------------|
| 🟢 `muda` | Hijau muda segar, tekstur lunak, ukuran kecil | **200** | **500+** |
| 🟤 `sedang` | Hijau tua, tekstur kaku & mengkilap, ukuran besar | **200** | **500+** |
| 🔴 `tua` | Kuning/merah/oranye/cokelat, kering & rapuh | **200** | **500+** |

### Langkah 3.2 — Tips Foto yang Bagus

**VARIASI adalah kunci!** Usahakan setiap foto punya variasi:

1. **Pencahayaan berbeda:**
   - ☀️ Outdoor siang terang
   - 🌥️ Outdoor mendung
   - 🌅 Sore hari
   - 💡 Indoor dengan lampu

2. **Sudut/angle berbeda:**
   - Tampak atas (top-down)
   - Tampak depan (45°)
   - Close-up detail
   - Agak jauh (ada background)

3. **Background berbeda:**
   - Di tangan
   - Di atas meja
   - Di tanah/rumput
   - Masih di pohon

4. **Kondisi berbeda:**
   - Daun utuh
   - Sedikit rusak/berlubang
   - Basah (habis hujan)
   - Kering

### Langkah 3.3 — Taruh ke Folder

```bash
# Contoh: copy foto ke folder yang sesuai
# Foto daun muda → dataset/muda/
# Foto daun sedang → dataset/sedang/
# Foto daun tua → dataset/tua/
```

**Format yang didukung:** `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`

### Langkah 3.4 — Cek Jumlah Dataset

Bisa cek jumlah foto di tiap folder:

```powershell
# PowerShell
(Get-ChildItem "dataset\muda" -File).Count
(Get-ChildItem "dataset\sedang" -File).Count
(Get-ChildItem "dataset\tua" -File).Count
```

> ⚠️ **PENTING:** Semua folder harus berisi minimal beberapa gambar. Folder kosong akan di-skip saat training! Kalau kelas cuma 2, model hanya bisa bedain 2 kelas.

---

## 🧠 4. Training Model

### Langkah 4.1 — Jalankan Training

```bash
# Pastikan virtual environment aktif!
# Dari folder root project:
py model/train.py
```

### Langkah 4.2 — Apa yang Terjadi saat Training

Training terdiri dari **2 fase**:

```
📌 Phase 1: FROZEN (±20 epoch)
   → Base model MobileNetV2 di-freeze
   → Hanya classification head yang di-train
   → Belajar fitur dasar klasifikasi

📌 Phase 2: FINE-TUNE (±30 epoch)
   → Top 30 layer MobileNetV2 di-unfreeze
   → Seluruh model di-fine-tune
   → Learning rate lebih kecil (1e-5)
```

> ⏳ **Estimasi waktu:** 10-30 menit (CPU), 3-10 menit (GPU)

### Langkah 4.3 — Output Training

Setelah training selesai, file-file berikut akan dibuat:

```
saved_model/
├── best_model.keras        ← Model utama (dipakai web app)
├── best_model.weights.h5   ← Weights saja
├── class_names.json        ← Daftar kelas yang di-train
└── plots/
    ├── phase_1_-_frozen.png        ← Grafik accuracy/loss fase 1
    ├── phase_2_-_fine-tune.png     ← Grafik accuracy/loss fase 2
    ├── confusion_matrix.png        ← Confusion matrix
    └── classification_report.txt   ← Laporan detail per kelas
```

### Langkah 4.4 — Baca Hasil Training

Setelah training selesai, perhatikan output di terminal:

```
🎯 FINAL VALIDATION ACCURACY: 0.9500 (95.00%)
📉 FINAL VALIDATION LOSS: 0.1234
```

**Panduan baca hasil:**
| Validation Accuracy | Artinya |
|-------------------|---------|
| **> 90%** | ✅ Bagus! Model siap dipakai |
| **70-90%** | ⚠️ Lumayan, tapi bisa ditingkatkan |
| **< 70%** | ❌ Kurang, tambah dataset atau cek kualitas foto |
| **100%** | ⚠️ Overfitting! Dataset terlalu kecil / terlalu mirip |

### Langkah 4.5 — Re-training (Jika Diperlukan)

Kalau hasil belum memuaskan:

1. **Tambah dataset** — lebih banyak variasi foto
2. **Hapus foto jelek** — foto blur, salah label, background dominan
3. **Jalankan ulang** `py model/train.py`

> Model lama akan di-overwrite otomatis.

---

## 📊 5. Evaluasi Model

### Langkah 5.1 — Jalankan Evaluasi

```bash
py model/evaluate.py
```

### Langkah 5.2 — Prediksi Gambar Tunggal

```bash
py model/predict.py path/ke/foto_daun.jpg
```

### Langkah 5.3 — Baca Confusion Matrix

Buka file `saved_model/plots/confusion_matrix.png`:

- **Diagonal** (kiri-atas → kanan-bawah) = prediksi **benar**
- **Off-diagonal** = prediksi **salah**
- Idealnya semua angka besar ada di diagonal

---

## 🌐 6. Menjalankan Web App

### Langkah 6.1 — Start Server

```bash
# Pastikan virtual environment aktif!
py web/app.py
```

Output yang diharapkan:

```
📂 Loading model...
✅ Model loaded! Classes: ['muda', 'sedang', 'tua']

==================================================
🌿 Deteksi Kematangan Daun Ketapang
   Server: http://localhost:5000
==================================================
```

### Langkah 6.2 — Buka di Browser

Buka salah satu URL berikut:

| URL | Kapan Pakai |
|-----|------------|
| `http://localhost:5000` | Di komputer yang sama |
| `http://<IP-kamu>:5000` | Dari HP/device lain di jaringan yang sama |

> 💡 IP lokal kamu biasanya muncul di terminal saat server start (contoh: `http://192.168.18.44:5000`)

### Langkah 6.3 — Matikan Server

Tekan `Ctrl + C` di terminal untuk menghentikan server.

---

## 🎮 7. Penggunaan Fitur

### 📷 Live Camera (Real-time Detection)

1. Klik tab **"📷 Live Camera"**
2. Klik **"Aktifkan Kamera"** → izinkan akses kamera
3. Arahkan kamera ke daun Ketapang
4. Sistem akan otomatis mendeteksi dan menampilkan:
   - **Bounding box** (kotak merah) di sekitar daun
   - **Label** (Muda/Sedang/Tua) + confidence
   - **Panel analisis** di bawah kamera

**Tombol di kamera:**
| Tombol | Fungsi |
|--------|--------|
| 📸 (kanan bawah) | Screenshot — simpan foto + bounding box |
| 🔄 (kanan atas) | Ganti kamera depan/belakang (HP) |

### 📁 Upload Gambar

1. Klik tab **"📁 Upload Gambar"**
2. Drag & drop foto, atau klik area upload
3. Klik **"🔍 Analisis Daun"**
4. Hasil muncul di bawah

### 📈 Statistik & Riwayat

- **Statistik Deteksi** — Menghitung total scan per kelas
- **Riwayat Analisis** — Log 50 scan terakhir dengan timestamp
- **Hapus** — Klik "🗑️ Hapus" untuk reset semua data

---

## 🔧 8. Troubleshooting

### `python` / `py` tidak dikenali

```
❌ 'python' is not recognized...
```

**Solusi:**
- Pakai `py` (Windows launcher) sebagai gantinya
- Atau aktifkan virtual environment dulu: `.\env\Scripts\Activate.ps1`
- Atau pakai full path: `.\env\Scripts\python.exe web/app.py`

### Module not found

```
❌ ModuleNotFoundError: No module named 'tensorflow'
```

**Solusi:**
- Pastikan virtual environment aktif `(env)` terlihat di terminal
- Install ulang: `pip install -r requirements.txt`

### Model belum ada

```
⚠️ Model belum ada: .../best_model.keras
```

**Solusi:**
- Training dulu: `py model/train.py`
- Pastikan folder `dataset/` sudah berisi gambar

### Kamera tidak bisa diakses

**Solusi:**
- Pastikan browser punya izin akses kamera
- Buka via `http://localhost:5000` (bukan IP) — beberapa browser memblokir kamera di non-HTTPS
- Coba browser lain (Chrome recommended)

### Prediksi salah / tidak akurat

**Solusi:**
- **Penyebab #1:** Dataset terlalu sedikit → tambah minimal 200+ per kelas
- **Penyebab #2:** Folder kelas kosong → semua kelas harus terisi
- **Penyebab #3:** Foto dataset kurang bervariasi → tambah variasi pencahayaan, sudut, background
- **Penyebab #4:** Foto salah label → cek ulang isi setiap folder

### Port 5000 sudah dipakai

```
❌ OSError: [Errno 98] Address already in use
```

**Solusi:**
```bash
# Matikan proses di port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# Atau jalankan di port lain — edit app.py baris terakhir:
# app.run(debug=True, host='0.0.0.0', port=5001)
```

---

## 🔄 Quick Reference — Perintah Penting

```bash
# 1. Aktifkan environment
.\env\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Training model
py model/train.py

# 4. Evaluasi model
py model/evaluate.py

# 5. Prediksi gambar tunggal
py model/predict.py foto_daun.jpg

# 6. Jalankan web app
py web/app.py

# 7. Buka di browser
# http://localhost:5000
```

---

## 📝 Catatan Penting

1. **Selalu aktifkan virtual environment** sebelum menjalankan perintah apapun
2. **Training ulang** diperlukan setiap kali dataset berubah
3. **Model lama** akan di-overwrite saat training ulang
4. **Debug mode** aktif secara default — server auto-restart saat edit kode Python
5. **Jangan gunakan debug mode di production** — ubah `debug=True` → `debug=False`
