# 🌿 LeafSense AI — Deteksi Kematangan Daun Ketapang

Sistem klasifikasi kematangan daun Ketapang (*Terminalia catappa*) menggunakan **MobileNetV2 Transfer Learning** dengan deployment berbasis web.

## 📋 Klasifikasi Kelas

| Kelas | Warna | Deskripsi |
|-------|-------|-----------|
| 🟢 **Muda** | Hijau muda segar | Tekstur lunak, halus, di ujung ranting |
| 🟤 **Sedang** | Hijau tua | Tekstur kaku, mengkilap, fotosintesis optimal |
| 🔴 **Tua** | Kuning/Merah/Oranye | Kering, rapuh, akan segera gugur |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Siapkan Dataset

Letakkan gambar daun ke dalam folder sesuai kelasnya:

```
dataset/
├── muda/       # Gambar daun muda
├── sedang/     # Gambar daun sedang/dewasa
└── tua/        # Gambar daun tua
```

> **Tips:** Minimal 100-200 gambar per kelas untuk hasil optimal.

### 3. Training Model

```bash
python model/train.py
```

Training terdiri dari 2 fase:
1. **Phase 1 (Frozen):** Train classification head, base model frozen
2. **Phase 2 (Fine-tune):** Unfreeze top 30 layers, fine-tune keseluruhan

Output:
- `saved_model/best_model.h5` — Model terbaik
- `saved_model/class_names.json` — Mapping kelas
- `saved_model/plots/` — Training curves & confusion matrix

### 4. Evaluasi Model

```bash
python model/evaluate.py
```

### 5. Prediksi Single Image

```bash
python model/predict.py path/to/daun.jpg
```

### 6. Jalankan Web App

```bash
python web/app.py
```

Buka browser: **http://localhost:5000**

## 🏗️ Struktur Project

```
├── dataset/            # Dataset gambar (user tambahkan sendiri)
│   ├── muda/
│   ├── sedang/
│   └── tua/
├── model/
│   ├── train.py        # Training pipeline
│   ├── evaluate.py     # Evaluasi & reporting
│   └── predict.py      # Prediksi CLI
├── saved_model/        # Output model
├── web/
│   ├── app.py          # Flask server
│   ├── templates/      # HTML
│   └── static/         # CSS, JS, uploads
├── requirements.txt
└── README.md
```

## ⚙️ Tech Stack

- **Model:** MobileNetV2 (TensorFlow/Keras Transfer Learning)
- **Backend:** Flask
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Evaluation:** scikit-learn, matplotlib, seaborn

## 📚 Referensi & Sumber

### Model & Transfer Learning
- **MobileNetV2 Paper:** Sandler, M., Howard, A., Zhu, M., Zhmoginov, A., & Chen, L. C. (2018). *MobileNetV2: Inverted Residuals and Linear Bottlenecks*. CVPR 2018. [arXiv:1801.04381](https://arxiv.org/abs/1801.04381)
- **TensorFlow Transfer Learning Tutorial:** [https://www.tensorflow.org/tutorials/images/transfer_learning](https://www.tensorflow.org/tutorials/images/transfer_learning)
- **Keras MobileNetV2 API:** [https://keras.io/api/applications/mobilenet/#mobilenetv2-function](https://keras.io/api/applications/mobilenet/#mobilenetv2-function)
- **TensorFlow Image Classification Guide:** [https://www.tensorflow.org/tutorials/images/classification](https://www.tensorflow.org/tutorials/images/classification)

### Data Augmentation & Training Strategy
- **Keras Data Augmentation Layers:** [https://www.tensorflow.org/tutorials/images/data_augmentation](https://www.tensorflow.org/tutorials/images/data_augmentation)
- **Fine-tuning Strategy (Freeze → Unfreeze):** [https://keras.io/guides/transfer_learning/](https://keras.io/guides/transfer_learning/)

### Evaluasi Model
- **scikit-learn Classification Report:** [https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html)
- **Confusion Matrix Visualization:** [https://seaborn.pydata.org/generated/seaborn.heatmap.html](https://seaborn.pydata.org/generated/seaborn.heatmap.html)

### Web Deployment
- **Flask Documentation:** [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- **Deploying ML Models with Flask:** [https://towardsdatascience.com/deploying-a-deep-learning-model-using-flask-3ec166ef59e8](https://towardsdatascience.com/deploying-a-deep-learning-model-using-flask-3ec166ef59e8)

### Domain Knowledge
- **Terminalia catappa (Ketapang):** [https://id.wikipedia.org/wiki/Ketapang](https://id.wikipedia.org/wiki/Ketapang)

## 📝 Tugas Besar PSI
