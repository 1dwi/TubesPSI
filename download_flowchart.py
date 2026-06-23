import base64
import urllib.request

mermaid_code = """flowchart TD
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
    
    style A fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff
    style P fill:#F44336,stroke:#D32F2F,stroke-width:2px,color:#fff
    style M fill:#FFC107,stroke:#FFA000,stroke-width:2px,color:#000
    style B fill:#E3F2FD,stroke:#1976D2
    style N fill:#E8F5E9,stroke:#388E3C
"""

# Encode the mermaid code to base64
encoded_string = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')

# Create the mermaid.ink URL
url = f"https://mermaid.ink/img/{encoded_string}"

# Download the image
print(f"Downloading flowchart from {url}...")
try:
    urllib.request.urlretrieve(url, "Flowchart_Metodologi.png")
    print("Berhasil disimpan sebagai Flowchart_Metodologi.png")
except Exception as e:
    print(f"Error: {e}")
