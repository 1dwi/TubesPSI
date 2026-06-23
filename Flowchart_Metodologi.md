# Alur Kerja Penelitian (Flowchart Metodologi)

Bos, ini adalah alur kerja sistem dari awal sampai akhir. Kamu bisa salin kode di bawah ini ke *Mermaid Live Editor* (https://mermaid.live/) untuk otomatis diubah jadi gambar yang bisa di-paste ke Word (Bab 3), atau tunjukkin aja alur ini ke dosennya kalau ditanya.

```mermaid
flowchart TD
    A([Mulai]) --> B[Pengumpulan Dataset Daun Ketapang]
    B --> C[Dataset Terkumpul: 1.922 Gambar]
    C --> D[Data Pre-processing & Augmentasi]
    
    subgraph Tahap Pre-processing
        D --> D1(Resize gambar ke 224x224)
        D1 --> D2(Random Flip & Rotation)
        D2 --> D3(Normalisasi Piksel)
    end
    
    D3 --> E[Pemisahan Dataset / Data Split]
    E --> |80%| F[Data Latih / Training Set]
    E --> |20%| G[Data Validasi / Validation Set]
    
    F --> H[Load Model MobileNetV2]
    H --> I[Fase 1: Training Frozen Base Model]
    I --> J[Fase 2: Fine-Tuning Top Layers]
    
    G --> K[Evaluasi Model tiap Epoch]
    K -.->|Early Stopping| J
    
    J --> L[Evaluasi Metrik Akhir]
    
    subgraph Evaluasi
        L --> L1(Confusion Matrix)
        L1 --> L2(Classification Report)
    end
    
    L2 --> M{Akurasi Memenuhi?}
    M -- Tidak --> D
    M -- Ya --> N[Simpan Model .keras]
    
    N --> O[Integrasi ke Sistem Web App Flask]
    O --> P([Selesai])
    
    %% Styling warna biar lebih cakep kalau dijadiin gambar
    style A fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff
    style P fill:#F44336,stroke:#D32F2F,stroke-width:2px,color:#fff
    style M fill:#FFC107,stroke:#FFA000,stroke-width:2px,color:#000
    style B fill:#E3F2FD,stroke:#1976D2
    style N fill:#E8F5E9,stroke:#388E3C
```

### Penjelasan Flowchart (Bisa dicopas ke Bab 3)
1. **Pengumpulan Dataset:** Gambar daun ketapang (muda, menguning, tua) dikumpulkan dengan total 1.922 data citra.
2. **Pre-processing:** Gambar diubah ukurannya menjadi 224x224 piksel menyesuaikan format *input* standar MobileNetV2, dan dilakukan augmentasi (rotasi/flip) untuk memperkaya variasi data.
3. **Pemisahan Dataset:** Dataset dibagi secara dinamis menggunakan rasio 80% data latih dan 20% data validasi.
4. **Pemodelan (MobileNetV2):** Model dilatih dalam 2 tahap. Tahap pertama membekukan (*freeze*) bobot asli ImageNet, tahap kedua melakukan *fine-tuning* pada layer atas agar model lebih sensitif terhadap pola tekstur daun.
5. **Evaluasi & Iterasi:** Model divalidasi dan diuji tingkat *error*-nya. Jika akurasi belum maksimal, model diulang, namun jika sudah stabil (memenuhi Early Stopping), model langsung disimpan.
6. **Integrasi Sistem:** Model `.keras` yang telah jadi, dihubungkan ke antarmuka pengguna berbasis Web menggunakan *framework* Flask.
