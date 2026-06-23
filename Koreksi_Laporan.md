# KOREKSI LAPORAN WORD (Tubes PSI)

Bos, di file `Laporan Tubes PSI hampir FIXX.docx` itu ada beberapa hal yang **TIDAK SESUAI** dengan aplikasi dan dataset asli yang kita bikin. Dosen pasti bakal nanya kalau angkanya nggak sinkron.

Berikut bagian-bagian yang harus diganti di Word kamu. Silakan *copy-paste* teks di bawah ini ke file Word-nya.

---

## 1. Bagian Abstrak & Abstract (Update Angka Dataset)
Di laporan tertulis dataset `±1.024` citra. Padahal aslinya cuma **531**. Ganti kalimatnya jadi begini:

**Abstrak (Indonesia):**
> Dataset penelitian terdiri dari 531 citra daun ketapang yang dibagi ke dalam tiga kelas, yaitu daun muda (295 citra), daun menguning (149 citra), dan daun tua (87 citra). Untuk menyeimbangkan dan memperbanyak data, dilakukan teknik augmentasi citra. Tahapan penelitian meliputi pengumpulan dataset, preprocessing citra, augmentasi data, pelatihan model, dan evaluasi performa model serta implementasinya pada aplikasi berbasis web. Model MobileNetV2 yang telah dilatih pada dataset ImageNet digunakan sebagai model dasar untuk meningkatkan performa klasifikasi.

**Abstract (English):**
> The research dataset consists of 531 ketapang leaf images divided into three classes: young leaves (295 images), yellowing leaves (149 images), and old leaves (87 images). To balance and increase the data, image augmentation techniques were performed. The research stages included dataset collection, image preprocessing, data augmentation, model training, performance evaluation, and implementation into a web-based application. The MobileNetV2 model trained on the ImageNet dataset was used as a baseline to improve classification performance.

---

## 2. Bagian "B. Dataset dan Klasifikasi Kelas" (Update Angka)
Ganti paragraf pertamanya jadi begini:

> Dataset yang digunakan dalam penelitian ini terdiri dari 531 citra daun ketapang (*Terminalia catappa*) yang dikumpulkan secara langsung menggunakan kamera smartphone pada kondisi pencahayaan alami. Pengambilan citra dilakukan dengan memperhatikan variasi sudut pengambilan gambar, latar belakang, dan intensitas cahaya. Dari total 531 citra, dataset dibagi menjadi daun muda sebanyak 295 citra, daun menguning sebanyak 149 citra, dan daun tua sebanyak 87 citra. Dataset ini kemudian dibagi menjadi 80% data latih (training) dan 20% data uji (validation).

---

## 3. Tambahkan Fitur Web App di "D. Implementasi Transfer Learning" (Ubah Judulnya)
Ubah judulnya menjadi **"D. Implementasi Model dan Aplikasi Web"** dan tambahkan paragraf ini di akhir bagian tersebut:

> Setelah model selesai dilatih dan dievaluasi, model klasifikasi diimplementasikan ke dalam aplikasi berbasis web menggunakan *framework* Flask. Antarmuka web dirancang interaktif dan modern untuk memudahkan pengguna melakukan klasifikasi secara langsung. Aplikasi ini memiliki fitur **Live Camera** untuk deteksi *real-time* via webcam, fitur **Upload Gambar**, serta fitur **Compare Mode** untuk membandingkan dua daun secara berdampingan. Selain itu, sistem juga dilengkapi dengan **Grad-CAM Heatmap** yang memvisualisasikan area pada citra daun yang menjadi fokus utama (diberi sorotan warna merah) oleh model dalam mengambil keputusan klasifikasi, sehingga hasil prediksi menjadi lebih transparan (Explainable AI).

---

## 4. Bagian "V. KESIMPULAN" (Update Kalimat Akhir)
Di kesimpulan kalimat akhirnya tertulis *"disarankan... mengimplementasikan model ke dalam aplikasi berbasis web"*. Padahal **KITA SUDAH BIKIN WEB-NYA!** Hapus kalimat itu, dan ganti paragraf terakhirnya jadi begini:

> Berdasarkan hasil yang diperoleh, dapat disimpulkan bahwa pendekatan transfer learning menggunakan MobileNetV2 merupakan metode yang efektif untuk klasifikasi tingkat kematangan daun ketapang. Model klasifikasi ini juga telah berhasil diintegrasikan ke dalam sistem aplikasi berbasis web interaktif. Aplikasi ini dilengkapi dengan fitur deteksi real-time melalui kamera, upload citra, Compare Mode, dan visualisasi Grad-CAM Heatmap untuk menjelaskan keputusan model. Sebagai pengembangan pada penelitian selanjutnya, disarankan untuk menambah jumlah dan variasi dataset dari berbagai kondisi lingkungan serta menguji penerapan model ini pada jenis tanaman herbal lainnya.
