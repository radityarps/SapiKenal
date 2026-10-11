# BAB V: KESIMPULAN DAN SARAN
## Sintesis Hasil Penelitian, Implikasi Rekayasa, dan Arah Riset Lanjutan

---

## 5.1 Kesimpulan

Berdasarkan hasil eksperimen komparatif, evaluasi statistik, interpretasi visual fenotipe, serta profiling komputasi tepi terhadap enam arsitektur convolutional neural network (CNN) dalam klasifikasi jenis sapi, dapat ditarik beberapa kesimpulan utama sebagai berikut:

1. **Arsitektur Paling Optimal (The Pareto-Optimal Model):**
   Arsitektur **MobileNetV3Large** terbukti secara empiris sebagai model paling optimal (*sweet spot*) untuk identifikasi jenis sapi. Model ini meraih akurasi puncak bersama sebesar **97.22% ± 4.03%**, Macro F1-Score **0.9698 ± 0.0435**, Macro Precision **0.9782**, dan Macro Recall **0.9679** pada pengujian *Stratified 5-Fold Cross-Validation*. Performa ini mengungguli model konvolusi residual klasik berbobot berat seperti ResNet50 (akurasi 95.81%) dan setara dengan arsitektur berkapasitas besar modern seperti EfficientNetV2S (97.22%) dan ConvNeXtTiny (97.19%).

2. **Pembuktian Statistik Berbasis Prinsip Occam's Razor:**
   Hasil pengujian *Pairwise McNemar's Test* pada tingkat signifikansi $\alpha = 0.05$ menghasilkan nilai $p \ge 0.5000$ di seluruh pasangan pengujian model (termasuk MobileNetV3Large vs ResNet50: $p = 0.6875$; vs ConvNeXtTiny: $p = 1.0000$). Hal ini membuktikan secara ilmiah bahwa penambahan kompleksitas parameter hingga sembilan kali lipat (dari 3.24 juta menjadi 28.02 juta parameter) **tidak memberikan peningkatan akurasi klasifikasi yang signifikan secara statistik**. Berdasarkan prinsip *Occam's Razor*, pemilihan model berbobot ringan (MobileNetV3Large) memiliki landasan metodologis yang kokoh untuk diimplementasikan sebagai model produksi.

3. **Verifikasi Keandalan Morfologis Visual (Explainable AI):**
   Analisis representasi visual berbasis **Grad-CAM** membuktikan bahwa MobileNetV3Large mengidentifikasi ras sapi berdasarkan ciri anatomi biologis yang valid, seperti:
   - **Punuk (*hump*) dan gelambir leher (*dewlap*)** pada Sapi Brahman.
   - **Cermin hidung berbingkai putih (*white muzzle*) dan tanduk** pada Sapi Bali.
   - **Bentuk postur berotot dan mantel hitam pekat** pada Sapi Brangus.
   - **Ketebalan daging punggung dan pinggul** pada Sapi Limusin.
   Peta panas aktivasi terkonsentrasi penuh pada tubuh ternak dan bebas dari bias latar belakang (*Clever Hans effect*), seperti rumput, tanah, atau pagar kandang.

4. **Kesiapan Komputasi Tepi untuk Aplikasi SapiKenal (TKT 5):**
   Pada format komputasi tepi **TensorFlow Lite (FP32)**, MobileNetV3Large mencatatkan kecepatan inferensi CPU sebesar **11.40 ms** ($\approx 87\text{ FPS}$) dan ukuran berkas instalasi hanya **12.30 MB**. Latensi ini **7.3× lebih cepat** dibanding EfficientNetV2S (83.70 ms), **9.1× lebih cepat** dibanding ResNet50 (103.29 ms), dan **18.1× lebih cepat** dibanding ConvNeXtTiny (206.05 ms). Ukuran yang ringkas dan responsivitas instan ini memvalidasi kelayakan implementasi luring mandiri (*offline-first*) pada aplikasi mobile **SapiKenal** untuk mendukung peternak di daerah perdesaan Kabupaten Boyolali yang minim akses internet.

---

## 5.2 Implikasi Praktis dan Teoritis

### 5.2.1 Implikasi Teoritis (Visi Komputer Peternakan)
- Penelitian ini memberikan kontribusi ilmiah berupa bukti empiris bahwa pada **rezim dataset terbatas (*small-sample regime*)**, arsitektur ringan berteknologi *Hardware-Aware Neural Architecture Search* (NAS) dengan blok *Squeeze-and-Excitation* (SE) memiliki kemampuan adaptasi fitur spasial yang lebih tahan terhadap *overfitting* dibandingkan arsitektur berbobot besar (*over-parameterized*).
- Menunjukkan pentingnya integrasi uji statistik formal (McNemar) dan interpretabilitas visual (Grad-CAM) dalam publikasi visi komputer terapan, guna mencegah klaim superioritas semu yang sering timbul pada evaluasi berulang.

### 5.2.2 Implikasi Praktis (Sektor Peternakan Boyolali)
- **Standardisasi Identifikasi Ternak:** Mengurangi ketergantungan pada intuisi subjektif pedagang pasar hewan, sehingga risiko salah taksir harga jual dan perselisihan transaksi ternak dapat ditekan secara signifikan.
- **Peningkatan Efisiensi Pakan dan Manajemen Bibit:** Peternak rakyat dapat segera menentukan formula ransum pakan dan target bobot karkas secara presisi sejak fase awal pemeliharaan berdasarkan kepastian jenis sapi hasil identifikasi sistem.
- **Dukungan Transformasi Digital (Smart Farming):** Memberikan purwarupa teknologi berbasis kecerdasan buatan yang siap pakai, hemat daya, dan dapat beroperasi tanpa internet di lingkungan peternakan rakyat.

---

## 5.3 Keterbatasan Penelitian

Penelitian ini memiliki sejumlah keterbatasan yang perlu diantisipasi pada tahapan pengembangan berikutnya:
1. **Cakupan Ras Sapi (Ruang Lingkup Tahap I):** Eksperimen komparasi saat ini terfokus pada empat ras sapi potong dan introduksi utama di Boyolali (Bali, Brahman, Brangus, Limusin). Ras sapi lokal lainnya seperti Sapi Jawa/PO dan Sapi Madura belum terintegrasi dalam pengujian komparasi ini akibat keterbatasan ketersediaan data citra teranotasi yang terverifikasi.
2. **Ketiadaan Kelas Penolakan (*Rejection Class*):** Pengujian benchmark saat ini mengasumsikan seluruh citra masukan adalah salah satu dari empat ras sapi, belum melibatkan kelas non-sapi (*negative/background class*) untuk menolak gambar acak yang bukan citra sapi.
3. **Kondisi Pengambilan Citra:** Dataset yang dievaluasi mayoritas memuat satu ekor sapi dalam bidang pandang kamera (*single-subject view*), sehingga belum menguji skenario ekstrem di mana terdapat kerumunan banyak sapi dalam satu bingkai pemotretan (*multi-subject clutter*).

---

## 5.4 Saran dan Arah Riset Lanjutan

Berdasarkan kesimpulan dan keterbatasan di atas, beberapa arah pengembangan lanjutan yang direkomendasikan adalah:

1. **Ekspansi Dataset Lapangan Multi-Ras:**
   Melakukan ekspansi pengumpulan data langsung dari peternakan rakyat dan pasar hewan di berbagai kecamatan di Kabupaten Boyolali untuk mencakup ras lokal tambahan (Sapi Jawa, Sapi Peranakan Ongole/PO, dan Sapi Madura) serta variasi sudut pandang pencahayaan malam/pagi hari.
2. **Integrasi Kelas Penolakan (*Out-of-Distribution Rejection*):**
   Menambahkan kelas `non_sapi` dan mekanisme pemutusan berbasis ambang batas probabilitas (*confidence thresholding*) pada model klasifikasi agar aplikasi SapiKenal dapat menolak citra manusia, objek kandang kosong, atau hewan lain secara andal.
3. **Kuantisasi Tingkat Lanjut (INT8 Post-Training Quantization):**
   Menerapkan teknik kuantisasi bilangan bulat 8-bit (INT8) pada model MobileNetV3Large. Berdasarkan proyeksi teoritis, kuantisasi INT8 berpotensi memangkas ukuran berkas dari **12.30 MB menjadi ~3.1 MB** dan menurunkan latensi inferensi CPU menjadi **<6 ms** tanpa penurunan akurasi yang signifikan.
4. **Pipeline Dua-Tahap (Deteksi Objek + Klasifikasi):**
   Mengintegrasikan model deteksi objek berbobot sangat ringan (seperti YOLOv8-Nano) untuk mendeteksi dan memotong (*bounding box crop*) area tubuh sapi secara otomatis sebelum citra diteruskan ke MobileNetV3Large. Pendekatan ini akan meningkatkan ketahanan identifikasi pada kondisi kandang padat dengan banyak objek pengganggu di latar belakang.
