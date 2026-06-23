# III. METODE

## A. Desain Sistem

Desain sistem pada penelitian ini menggambarkan struktur *pipeline end-to-end* pengolahan citra digital untuk klasifikasi tingkat kematangan daun ketapang (*Terminalia catappa*). Berbeda dengan pemrosesan konvensional, sistem ini mengadopsi pendekatan linier terstruktur guna memastikan data mentah dari lapangan dapat ditransformasikan secara optimal hingga menghasilkan model siap pakai. Alur linier sistem ini disusun secara bertahap dengan mengacu langsung pada skema arsitektur sistem yang dikembangkan, meliputi 7 tahapan utama sebagai berikut:

1. **Pengumpulan Dataset:** Proses pengambilan sampel gambar daun ketapang langsung dari pohonnya di area lapangan dengan memanfaatkan sensor kamera perangkat bergerak (*smartphone*).
2. **Preprocessing:** Tahap penyeragaman karakteristik data mentah dengan melakukan *resizing* dimensi matriks citra menjadi 224×224 piksel serta menerapkan normalisasi skala nilai piksel ke rentang [−1, 1] sesuai standar *preprocessing* MobileNetV2.
3. **Augmentasi Data:** Proses manipulasi sintetis untuk melipatgandakan variasi data latih secara acak menggunakan metode transformasi geometris dan fotometris tanpa mengubah pelabelan asli kelas citra.
4. **Transfer Learning MobileNetV2:** Mengintegrasikan arsitektur *backbone* MobileNetV2 dengan memuat parameter bobot (*weights*) yang telah terlatih sebelumnya (*pretrained*) berbasis basis data ImageNet.
5. **Training Model:** Melakukan proses pembelajaran komputasi pada arsitektur jaringan saraf, terintegrasi dengan fungsi regularisasi *Early Stopping* untuk mendeteksi titik jenuh nilai *validation accuracy*.
6. **Evaluasi Model:** Menguji kekuatan generalisasi model akhir menggunakan data validasi (*validation set*) yang diukur secara kuantitatif melalui instrumen akurasi, presisi, *recall*, dan *F1-score*.
7. **Model Klasifikasi:** Luaran sistem berupa berkas biner berbobot optimal (format `.keras`) yang siap diimplementasikan untuk kebutuhan pengerahan (*deployment*) sistem otomatisasi di lapangan.

---

## B. Dataset, Perangkat Pengumpul, dan Klasifikasi Kelas

Dataset yang digunakan dalam penelitian ini berjumlah total kurang lebih **2.418 citra** digital daun ketapang (*Terminalia catappa*). Seluruh sampel data diambil secara mandiri di lapangan pada kondisi pencahayaan alami (*ambient outdoor lighting*) untuk merepresentasikan variasi lingkungan riil.

Guna memenuhi catatan standarisasi instrumen pengambilan data, proses akuisisi citra digital dilakukan secara kolektif menggunakan tiga jenis perangkat komersial berbeda untuk meningkatkan keberagaman karakteristik sensor (*sensor variability*). Spesifikasi teknis dari ketiga perangkat kamera *smartphone* tersebut dirinci pada Tabel 3.1 berikut.

### Tabel 3.1 Spesifikasi Teknis Perangkat Kamera Pengumpul Citra

| Parameter Sensor | Samsung Galaxy A50s | Samsung Galaxy A33 5G | Realme 12 5G |
|---|---|---|---|
| Resolusi Kamera Utama | 48 MP | 48 MP | 108 MP (Mode standar 48 MP) |
| Aperture | f/2.0 | f/1.8 (OIS) | f/1.75 |
| Panjang Fokus | 26 mm (wide) | 26 mm (wide) | 24 mm (wide) |
| Format Output Citra | RGB (.jpg / .jpeg) | RGB (.jpg / .jpeg) | RGB (.jpg / .jpeg) |
| Kondisi Pencahayaan | Alami (Outdoor, 09.00–15.00 WIB) | Alami (Outdoor, 09.00–15.00 WIB) | Alami (Outdoor, 09.00–15.00 WIB) |
| Jarak Objek ke Kamera | 15–25 cm | 15–25 cm | 15–25 cm |

Penggunaan kombinasi sensor dari tiga manufaktur perangkat yang berbeda ini memastikan bahwa model jaringan saraf tidak hanya mengenali pola daun pada satu karakteristik lensa tunggal, melainkan adaptif terhadap perbedaan temperatur warna (*white balance*) dan kontras bawaan perangkat keras.

Data tersebut dibagi ke dalam **3 kategori kelas** pertumbuhan berdasarkan variasi morfologi dan perubahan kandungan pigmen klorofil tanaman. Setiap kelas diwakili oleh jumlah citra yang telah diseimbangkan (*balanced dataset*) guna menghindari bias klasifikasi selama proses *training*:

1. **Daun Muda (*Young Leaves*):** Merupakan representasi daun pada fase awal vegetatif. Karakteristik visual ditandai dengan dominasi warna hijau cerah yang merata, struktur helaian daun yang tipis, serta permukaan tekstur epidermis yang cenderung halus tanpa bercak degradasi pigmen.
2. **Daun Menguning (*Yellowing Leaves*):** Merupakan fase transisi biologis akibat berkurangnya konsentrasi zat hijau daun (klorofil). Karakteristik visual memperlihatkan perpaduan gradasi warna hijau kekuningan hingga kuning oranye pada sebagian besar lamina daun.
3. **Daun Tua (*Old Leaves*):** Merupakan fase akhir penuaan sel jaringan daun (*senescence*). Karakteristik visual ditandai dengan perubahan warna secara drastis menjadi cokelat tua, merah tua, atau keunguan, disertai tekstur permukaan yang kering, kasar, dan mengeras akibat akumulasi senyawa metabolit sekunder.

Seluruh dataset dipisahkan secara otomatis menggunakan fungsi `validation_split` pada TensorFlow dengan rasio pembagian **80% untuk data latih (*training set*)** dan **20% untuk data validasi (*validation set*)**. Pembagian dilakukan secara acak (*random seed*: 42) untuk menjamin reprodusibilitas eksperimen.

> **[DIHAPUS dari versi sebelumnya]:** Klaim pembagian "10% validasi + 10% test set" tidak sesuai dengan implementasi kode. Dalam penelitian ini **tidak terdapat** *test set* terpisah; evaluasi dilakukan sepenuhnya menggunakan *validation set* (20%).

---

## C. Preprocessing Citra dan Augmentasi Data

Tahap pra-pemrosesan citra dilakukan secara sekuensial untuk mengubah berkas gambar mentah menjadi bentuk matriks tensor numerik yang kompatibel dengan arsitektur komputasi *deep learning*. Langkah pertama adalah proses *resizing* geometri citra dari resolusi bawaan kamera menjadi dimensi seragam **224×224 piksel** menggunakan algoritma interpolasi bilinear. Proses ini krusial untuk menyelaraskan dimensi *input* data dengan gerbang matriks lapisan pertama MobileNetV2.

Langkah kedua adalah normalisasi intensitas nilai piksel. Normalisasi dilakukan menggunakan fungsi bawaan `preprocess_input` dari masing-masing arsitektur:
- **MobileNetV2** (Skenario A & B): Mengonversi rentang nilai piksel integer [0, 255] menjadi rentang **[−1, 1]** melalui operasi matematis: `x = x / 127.5 − 1`.
- **ResNet50** (Skenario C): Menerapkan pra-pemrosesan gaya *Caffe*, yaitu mengurangi nilai rata-rata RGB dan mengonversi urutan kanal dari RGB ke BGR.

Normalisasi ini berfungsi untuk menstabilkan pergerakan nilai gradien, menekan fluktuasi komputasi, serta mempercepat proses pencapaian konvergensi *loss function* saat fase pelatihan jaringan.

Untuk mengatasi keterbatasan variasi persebaran data di lapangan dan meminimalkan risiko gejala *overfitting*, diterapkan teknik augmentasi data dinamis pada *training set* secara *on-the-fly*. Teknik transformasi fotometris dan geometris yang dikonfigurasikan adalah sebagai berikut:

1. **Pencerminan Acak (*Random Flip*):** Membalik citra secara **horizontal dan vertikal** secara acak untuk menghasilkan variasi orientasi sudut pandang objek daun.
2. **Rotasi Acak (*Random Rotation*):** Memutar posisi citra dengan faktor rotasi **0,3** (setara rentang ±108 derajat) untuk menyimulasikan berbagai kemungkinan orientasi daun saat difoto di lapangan.
3. **Perbesaran Acak (*Random Zoom*):** Melakukan efek perbesaran atau pengecilan skala spasial sebesar **20%** untuk memberikan toleransi variasi jarak pemotretan.
4. **Penyesuaian Kecerahan (*Random Brightness*):** Memanipulasi tingkat lumen cahaya dengan faktor variasi **20%** guna melatih model agar tetap kebal (*robust*) terhadap perubahan intensitas bayangan matahari.
5. **Penyesuaian Kontras (*Random Contrast*):** Mengubah rasio perbedaan tingkat terang-gelap citra secara acak dengan faktor variasi **20%** untuk meningkatkan ketahanan model terhadap kondisi pencahayaan yang tidak seragam.

---

## D. Konfigurasi Skenario Eksperimen Transfer Learning

Penelitian ini menerapkan arsitektur MobileNetV2 sebagai *backbone network* utama karena struktur penyusunnya yang efisien dan cocok untuk *edge device*, memanfaatkan operasi *depthwise separable convolution* serta komponen *inverted residual blocks* dengan *linear bottleneck*.

Guna menganalisis efektivitas pengaruh kedalaman transfer pengetahuan (*transfer learning*) dan perubahan nilai parameter hiperparameter terhadap performa klasifikasi daun ketapang, penelitian ini merancang **3 Skenario Eksperimen** yang berbeda secara komparatif:

### 1. Skenario A — MobileNetV2 *Feature Extractor* (Baseline)

- **Mekanisme:** Menggunakan model MobileNetV2 murni sebagai ekstraktor fitur statis. Seluruh **154 lapisan dasar** (*base layers*) bawaan ImageNet dibekukan secara total (*frozen status*). Pelatihan ulang hanya dilakukan pada lapisan klasifikasi baru (*classifier head*) yang ditambahkan di bagian akhir jaringan. Skenario ini hanya menjalankan **1 fase pelatihan** (tanpa fase *fine-tuning*).
- **Hiperparameter:** Nilai *Learning Rate* ditetapkan sebesar 1×10⁻³ menggunakan algoritma optimasi Adam. Skenario ini bertujuan sebagai pengujian dasar (*baseline*) untuk mengukur seberapa relevan fitur visual umum ImageNet terhadap domain klasifikasi daun ketapang tanpa adaptasi bobot apapun.

### 2. Skenario B — MobileNetV2 *Partial Fine-Tuning* (Model Utama)

- **Mekanisme:** Menerapkan strategi pematangan adaptif (*Fine-Tuning* Parsial) dengan **2 fase pelatihan**. Pada Fase 1, seluruh lapisan MobileNetV2 dibekukan dan hanya *classifier head* yang dilatih (sama seperti Skenario A). Pada Fase 2, **30 lapisan terakhir** (*top 30 layers*) dari *backbone* MobileNetV2 dibuka kuncinya (*unfreezing*) dan dilatih kembali bersama-sama dengan lapisan klasifikasi menggunakan data daun ketapang.
- **Hiperparameter:** Fase 1 menggunakan *Learning Rate* sebesar 1×10⁻³, kemudian pada Fase 2 diturunkan menjadi 1×10⁻⁴ untuk menjaga kestabilan pembaruan gradien agar tidak merusak bobot yang sudah optimal dari ImageNet. Skenario ini merupakan konfigurasi utama yang diharapkan menghasilkan performa tertinggi.

### 3. Skenario C — ResNet50 (Arsitektur Pembanding)

- **Mekanisme:** Sebagai parameter komparasi performa antar-arsitektur, skenario ketiga mengganti keseluruhan *backbone network* menggunakan arsitektur **ResNet50** dengan skema pelatihan **2 fase** yang serupa dengan Skenario B. Pada Fase 2, **30 lapisan terakhir** ResNet50 dibuka kuncinya untuk di-*fine-tune*. Skenario ini bertujuan membuktikan apakah arsitektur yang lebih besar dan dalam selalu menghasilkan performa yang lebih baik.
- **Hiperparameter:** Fase 1 menggunakan *Learning Rate* 1×10⁻³, kemudian pada Fase 2 diturunkan menjadi 1×10⁻⁵ (lebih kecil dari Skenario B) untuk menjaga stabilitas pembaruan gradien pada struktur lapisan ResNet50 yang jauh lebih dalam (sekitar 175 layer dengan ±25 juta parameter).

---

### Arsitektur *Classifier Head*

Pada bagian akhir blok klasifikasi (*classifier head*) ketiga skenario di atas, dipasang struktur arsitektur lapisan seragam sebagai berikut:

1. **Global Average Pooling (GAP):** Meratakan matriks spasial fitur menjadi vektor satu dimensi untuk mengurangi parameter latih secara efisien.
2. **Batch Normalization (1):** Menormalisasi distribusi keluaran antar-*batch* untuk menstabilkan dan mempercepat proses pelatihan.
3. **Dropout Layer (1):** Ditetapkan pada koefisien nilai **0,5** (mematikan 50% neuron secara acak tiap *epoch*) sebagai teknik regularisasi lapis pertama.
4. **Dense Layer (*Fully Connected*):** Memiliki kapasitas **128 neuron** yang dikombinasikan dengan fungsi aktivasi non-linear *Rectified Linear Unit* (ReLU).
5. **Batch Normalization (2):** Normalisasi distribusi tambahan setelah lapisan Dense untuk memperkuat stabilitas gradien.
6. **Dropout Layer (2):** Ditetapkan pada koefisien nilai **0,3** (mematikan 30% neuron) sebagai teknik regularisasi lapis kedua guna lebih menekan risiko *overfitting*.
7. **Dense Output Layer:** Memiliki **3 gerbang neuron keluaran** yang mengimplementasikan fungsi aktivasi *Softmax* untuk menghasilkan distribusi nilai probabilitas prediksi kelas kematangan daun ketapang (Muda, Menguning, Tua).

---

### Mekanisme *Callback* Pelatihan

Seluruh jalannya proses pelatihan pada ketiga skenario dikontrol oleh tiga mekanisme *callback* otomatis:

1. **Early Stopping:** Memantau nilai ***validation accuracy*** sebagai acuan interupsi otomatis. Parameter *patience* ditetapkan sebesar **7 epoch** — apabila tidak terjadi peningkatan akurasi validasi selama 7 epoch berturut-turut, proses pelatihan akan dihentikan secara otomatis dan bobot model dikembalikan ke titik terbaik (*restore_best_weights*).
2. **Model Checkpoint:** Menyimpan bobot model terbaik secara otomatis setiap kali nilai *validation accuracy* mencatat rekor baru selama proses pelatihan berlangsung.
3. **Reduce Learning Rate on Plateau:** Menurunkan nilai *learning rate* secara otomatis dengan faktor pengali **0,5** apabila nilai *validation loss* tidak mengalami penurunan selama **3 epoch** berturut-turut, dengan batas minimum *learning rate* sebesar 1×10⁻⁷.

> **[KOREKSI dari versi sebelumnya]:**
> - *Early Stopping* memantau **validation accuracy** (bukan validation loss).
> - Nilai *patience* adalah **7** (bukan 10).
> - *Classifier head* menggunakan **128 neuron** (bukan 256) dengan **2 lapis Dropout** (0,5 dan 0,3) serta **2 lapis Batch Normalization**.
> - Augmentasi mencakup **5 teknik** (termasuk *Random Contrast* dan *Vertical Flip*), bukan 4.
> - Pembagian dataset adalah **80:20** (training:validation), bukan 80:10:10.
