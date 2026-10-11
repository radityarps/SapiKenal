# Studi Komparasi Arsitektur Convolutional Neural Network untuk Klasifikasi Ras Sapi Berbasis Citra Digital pada Komputasi Tepi

## 1. PENDAHULUAN

Sektor peternakan ruminansia memegang peran fundamental dalam ketahanan pangan hewani nasional dan perekonomian pedesaan Indonesia. Kabupaten Boyolali, Jawa Tengah, menempati kedudukan strategis sebagai salah satu lumbung sapi terkemuka di Pulau Jawa dengan populasi puluhan ribu ekor sapi perah dan sapi potong yang terkonsentrasi di sentra peternakan rakyat serta pasar hewan regional [1], [2]. Setiap ras sapi memiliki karakteristik genetik, kapasitas adaptasi iklim, dan potensi produktivitas yang berbeda secara mendasar. Sapi Bali (*Bos javanicus domesticus*) memiliki efisiensi karkas tinggi dan daya adaptasi pakan kasar; Sapi Brahman (*Bos indicus*) memiliki ketahanan cuaca tropis berkat punuk dan gelambir leher; Sapi Brangus (*crossbreed* Brahman × Angus) memiliki laju pertambahan bobot harian tinggi; sedangkan Sapi Limusin (*Bos taurus*) unggul dalam volume perototan daging bernilai ekonomis tinggi [1]. Kepastian identitas ras ternak menjadi parameter penentu dalam penetapan formulasi ransum pakan, manajemen pemuliaan bibit (*breeding*), hingga penaksiran harga jual ternak di pasar hewan.

Kendati demikian, praktik identifikasi jenis sapi di tingkat peternakan rakyat dan pasar tradisional (seperti Pasar Hewan Sunggingan Boyolali) masih mengandalkan pengamatan visual subjektif peternak dan pedagang. Metode konvensional ini memiliki kerentanan tinggi terhadap bias pengamat, rawan kekeliruan identifikasi pada fase pertumbuhan sapi muda akibat kemiripan fenotipe antar-ras, serta tidak memiliki dokumentasi digital yang objektif [6]. Pemanfaatan sistem informasi berbasis kecerdasan buatan (*Artificial Intelligence*) menawarkan solusi otomatisasi identifikasi berbasis citra digital. Namun, penerapan di pedesaan Boyolali menghadapi tantangan infrastruktur yang nyata: konektivitas internet seluler di area kandang seringkali tidak stabil (*blind spot*), sementara mayoritas peternak menggunakan perangkat ponsel pintar berspesifikasi menengah ke bawah (*low-to-mid range devices*) [9]. Oleh karena itu, sistem informasi yang dikembangkan menuntut arsitektur **luring mandiri (*offline-first*)**, di mana model visi komputer dieksekusi secara lokal pada prosesor ponsel (*mobile edge computing*) tanpa ketergantungan jaringan internet.

Penelitian terdahulu mengenai visi komputer pada peternakan sapi telah mengeksplorasi pelacakan individu dan biometrik wajah (Qiao dkk. [10], Andrew dkk. [8], Weng dkk. [28]), deteksi multi-ras berbasis transformer (Li dkk. [3]), pengenalan ras spesifik (de Lima Weber dkk. [27], Mathews & Misra [5], BharatPashu [9], Pathak & Prakash [11], Sahu & Khanna [12], Jain dkk. [13]), serta identifikasi kerbau lokal Indonesia menggunakan YOLOv9 (Manga' dkk. [7]). Meskipun demikian, telaah literatur menunjukkan sejumlah kesenjangan riset (*research gaps*):
1. **Ketiadaan Komparasi Lintas Paradigma Arsitektur yang Komprehensif:** Belum ada penelitian yang membandingkan arsitektur CNN ringan berbasis *Hardware-Aware Neural Architecture Search* (MobileNetV3Large), arsitektur skala kompon (EfficientNetB0, EfficientNetV2S), arsitektur residual klasik (ResNet50), dan arsitektur konvolusi modern berprinsip Vision Transformer (ConvNeXtTiny) secara setara (*controlled benchmark*) pada citra ras sapi di Indonesia.
2. **Kelemahan Validasi Data Tunggal (*Single Split Bias*):** Mayoritas studi terdahulu hanya mengandalkan pembagian data latih-uji satu kali (*single split*), yang rentan terhadap variasi acak sampling (*sampling bias*) pada ukuran dataset terbatas.
3. **Kurangnya Pengujian Signifikansi Statistik Formal:** Perbedaan performa model umumnya diklaim semata-mata berdasarkan selisih persentase akurasi nominal, tanpa uji statistik formal (seperti uji McNemar) untuk membuktikan signifikansi ilmiah penambahan parameter.
4. **Ancaman Bias Latar Belakang dan Minimnya Profiling Komputasi Tepi:** Sebagian besar literatur belum memverifikasi apakah model mengunci ciri morfologi ternak atau terdistorsi artefak latar belakang kandang (*Clever Hans Effect*), serta jarang melaporkan profil inferensi riil pada format komputasi tepi (*TensorFlow Lite CPU latency*).

Untuk mengatasi kesenjangan tersebut dan menyediakan mesin inferensi cerdas (*intelligent engine*) bagi sistem informasi mobile **SapiKenal** pada Tingkat Kesiapterapan Teknologi **TKT 5**, penelitian ini menyajikan studi komparatif terstandarisasi terhadap enam arsitektur CNN modern. Dalam peta jalan jangka panjang yang menargetkan enam ras sapi di Boyolali (Sapi Jawa, Madura, Bali, Brahman, Brangus, Limusin), penelitian ini memfokuskan evaluasi model pada **empat ras representatif dengan disparitas morfologi fenotipik paling kontras** (Bali, Brahman, Brangus, dan Limusin) sebagai tolok ukur ketahanan representasi visual arsitektur CNN. 

Kontribusi utama penelitian ini mencakup: (1) evaluasi komparatif multi-arsitektur terkontrol menggunakan *Stratified 5-Fold Cross-Validation* dan protokol *Two-Phase Transfer Learning*, (2) pembuktian statistik formal menggunakan *Pairwise McNemar's Test* yang menegakkan prinsip *Occam's Razor* dalam pemilihan model produksi, (3) verifikasi interpretabilitas visual berbasis Grad-CAM untuk membuktikan fokus atensi pada ciri biologis ternak, serta (4) pengukuran efisiensi komputasi tepi (*TFLite model size* dan latensi CPU milidetik) untuk menjamin kesiapan deployment luring pada aplikasi mobile peternak.

---

## 2. METODE PENELITIAN

### 2.1 Alur Penelitian Berbasis CRISP-DM
Metodologi penelitian ini mengadopsi kerangka kerja *Cross-Industry Standard Process for Data Mining* (CRISP-DM) yang diselaraskan dengan kebutuhan rekayasa perangkat lunak sistem informasi peternakan. Alur metodologi terbagi ke dalam lima fase sistematis: *Data Acquisition*, *Data Preparation & Augmentation*, *Two-Phase Modeling*, *Evaluation & Statistical Testing*, serta *Edge Deployment Profiling*, sebagaimana diilustrasikan pada Gambar 1.

```
+---------------------------------------------------------------------------------------------------+
|                                     ALUR METODOLOGI PENELITIAN                                    |
+---------------------------------------------------------------------------------------------------+
|  [1. Akuisisi Citra]       --> 143 citra lapangan 4 ras sapi di Boyolali (Bali, Brahman, Brangus, |
|                                 Limusin) dengan variasi sudut lateral, frontal, dan pencahayaan.  |
|  [2. Preparasi Data]       --> Resize 224x224x3, normalisasi kanal, partisi Stratified 5-Fold CV  |
|                                 (80% latih / 20% validasi terisolasi), augmentasi dinamis.       |
|  [3. Pemodelan 2-Fase]     --> 6 Arsitektur CNN: MobileNetV3L, MobileNetV2, EffNetB0, EffNetV2S,  |
|                                 ConvNeXtTiny, ResNet50.                                           |
|                                 Fase 1: Feature Extraction (Frozen, lr=1e-3, <=30 epoch).         |
|                                 Fase 2: Fine-Tuning (Top 30% Unfrozen, lr=1e-5, <=20 epoch).      |
|  [4. Evaluasi & XAI]       --> Akurasi, Macro F1/P/R, Uji McNemar (alpha=0.05), Grad-CAM.         |
|  [5. Profiling Edge]       --> Ekspor TFLite FP32, uji ukuran berkas (MB) dan latensi CPU (ms).   |
+---------------------------------------------------------------------------------------------------+
```
*Gambar 1. Kerangka kerja eksperimen komparasi model CNN dan profiling deployment.*

### 2.2 Karakteristik Dataset dan Verifikasi Morfologi
Dataset terdiri dari 143 citra resolusi tinggi yang dikumpulkan langsung dari peternakan rakyat dan pasar hewan di Kabupaten Boyolali. Citra mencakup variasi kondisi alami (*in-the-wild*), meliputi latar belakang kandang bambu/kayu, lantai tanah/semen, serta pencahayaan alami pagi hingga sore hari. Seluruh citra diverifikasi anotasi labelnya bersama tenaga praktisi peternakan berdasarkan ciri morfologi fenotipik standar:
- **Sapi Bali** ($n = 31$): Postur tubuh kompak, warna bulu merah bata (betina/muda) atau hitam pekat (jantan dewasa), cermin pantat putih (*white rump patch*), dan keempat kaki putih dari lutut ke bawah (*white socks*).
- **Sapi Brahman** ($n = 30$): Punuk (*hump*) menonjol di atas bahu, lipatan gelambir leher (*dewlap*) yang longgar memanjang dari dagu ke dada, telinga panjang terkulai melengkung, dan warna bulu putih keabu-abuan.
- **Sapi Brangus** ($n = 42$): Mantel bulu hitam legam menyeluruh, tubuh silindris padat berotot, kepala tanpa tanduk (*polled*), dan punuk sangat kecil (*moderate hump*).
- **Sapi Limusin** ($n = 40$): Postur tubuh besar dan panjang, otot paha dan punggung sangat tebal (*muscularity*), warna bulu cokelat keemasan (*golden-red*), serta lingkaran warna terang di sekitar mata dan moncong.

### 2.3 Protokol Validasi Silang dan Augmentasi Citra
Untuk mencegah bias pemilihan sampel (*sampling bias*) dan menjamin seluruh citra dievaluasi secara independen, data dipartisi menggunakan **Stratified 5-Fold Cross-Validation**. Pada setiap *fold*, proporsi kelas dipertahankan seimbang dengan rasio 80% data latih ($n \approx 114$) dan 20% data validasi/uji ($n \approx 29$). Pemisahan dilakukan sebelum proses augmentasi guna mencegah kebocoran data (*data leakage*).

Seluruh citra distandardisasi ke dimensi $224 \times 224 \times 3$ piksel dan dinormalisasi sesuai format prapemrosesan masing-masing arsitektur *backbone*. Selama pelatihan data latih, diaplikasikan augmentasi citra dinamis *on-the-fly*: rotasi acak ($\pm 25^\circ$), pergeseran lebar/tinggi ($\pm 15\%$), pembalikan horizontal (*horizontal flip*), pembesaran (*zoom* $\pm 15\%$), serta penyesuaian kecerahan acak ($[0.85, 1.15]$).

### 2.4 Arsitektur CNN Kandidat
Enam arsitektur CNN yang mewakili empat paradigma desain spasial dievaluasi secara setara:
1. **MobileNetV3Large** [17]: Model ringan hasil pencarian otomatis *Hardware-Aware Neural Architecture Search* (NAS) yang dilengkapi blok *Squeeze-and-Excitation* (SE) dan aktivasi *hard-swish* (3.24M parameter).
2. **MobileNetV2** [18]: Model konvolusi *depthwise separable* dengan blok residual terbalik (*inverted residuals*) dan *linear bottlenecks* (2.59M parameter).
3. **EfficientNetB0** [19]: Arsitektur berbasis modul MBConv dengan penskalaan serentak kedalaman, lebar, dan resolusi (*compound scaling*) (4.38M parameter).
4. **EfficientNetV2S** [20]: Penskalaan efisien generasi kedua yang menyematkan modul *Fused-MBConv* pada lapisan awal untuk mempercepat inferensi (20.66M parameter).
5. **ConvNeXtTiny** [21]: Arsitektur konvolusi murni berprinsip desain Vision Transformer (kernel spasial besar $7\times 7$, rasio tahap 1:1:3:1, *Layer Normalization*, aktivasi GELU) (28.02M parameter).
6. **ResNet50** [22]: Arsitektur residual klasik dengan koneksi pintas identitas (*identity skip connection*) 50 lapis (24.11M parameter).

### 2.5 Protokol Pelatihan Dua Fase (*Two-Phase Transfer Learning*)
Seluruh arsitektur menggunakan bobot awal *pretrained* ImageNet-1k. Kepala klasifikasi (*classification head*) dirancang seragam: *Global Average Pooling 2D*, lapisan *Dense* 128 unit (ReLU), *Dropout* 0.3 untuk regulasi penalti, dan lapisan *Dense* 4 unit (aktivasi *Softmax*). Pelatihan dieksekusi dalam dua fase terkalibrasi:
- **Fase 1 (Feature Extraction):** Seluruh bobot *backbone* dibekukan (*frozen*). Hanya lapisan kepala klasifikasi yang dilatih selama maksimum 30 epoch menggunakan optimizer AdamW, laju pembelajaran awal $\eta = 10^{-3}$, *weight decay* $10^{-4}$, dan ukuran batch 16.
- **Fase 2 (Calibrated Fine-Tuning):** 30% lapisan teratas dari *backbone* dicairkan (*unfrozen*), sementara 70% lapisan dasar tetap dibekukan untuk mempertahankan representasi fitur umum. Model dilatih kembali selama maksimum 20 epoch dengan laju pembelajaran diperkecil menjadi $\eta = 10^{-5}$ guna mencegah rusaknya representasi bobot awal (*catastrophic forgetting*). Mekanisme *ReduceLROnPlateau* (faktor 0.5, kesabaran 3 epoch) dan *Early Stopping* (kesabaran 6 epoch) diaktifkan untuk menjaga stabilitas konvergensi.

### 2.6 Metrik Evaluasi, Uji Statistik McNemar, dan Profiling Komputasi Tepi
Kinerja model dievaluasi menggunakan metrik standar klasifikasi multi-kelas: Akurasi, Macro Precision, Macro Recall, dan Macro F1-Score, yang dilaporkan dalam bentuk rerata dan simpangan baku (*Mean ± Std*) lintas 5 lipatan.

Untuk memvalidasi apakah perbedaan klasifikasi antar-model bersifat signifikan secara saintifik, dilakukan pengujian hipotesis statistik non-parametrik **Pairwise McNemar's Test** menggunakan tabel kontingensi $2 \times 2$. Nilai statistik uji dihitung dengan koreksi kontinuitas Edwards:
$$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$$
di mana $b$ adalah jumlah sampel yang diprediksi benar oleh Model A namun salah oleh Model B, dan $c$ adalah jumlah sampel yang diprediksi salah oleh Model A namun benar oleh Model B. Tingkat signifikansi ditetapkan pada $\alpha = 0.05$. Hipotesis nol ($H_0$) menyatakan bahwa kedua model memiliki tingkat kesalahan yang identik; $H_0$ ditolak jika nilai $p < 0.05$.

Untuk interpretabilitas fitur visual, diimplementasikan algoritma **Grad-CAM** [23] pada lapisan konvolusi terakhir masing-masing model untuk menghasilkan peta panas atensi (*activation heatmaps*). Profiling komputasi tepi dilakukan dengan mengonversi model terlatih ke format biner *TensorFlow Lite (TFLite) FP32*. Pengukuran latensi inferensi dieksekusi pada CPU multi-core (rerata 100 iterasi setelah 10 siklus *warm-up*).

---

## 3. HASIL DAN PEMBAHASAN

### 3.1 Perbandingan Performa Komparatif 6 Arsitektur CNN
Tabel 1 menyajikan hasil komparasi menyeluruh keenam arsitektur CNN pada tahap akhir Fase 2 (*Fine-Tuning*), diurutkan berdasarkan kombinasi akurasi, efisiensi memori, dan kecepatan inferensi.

#### Tabel 1. Rangkuman Master Komparasi Performa Klasifikasi dan Efisiensi Deployment

| Peringkat | Arsitektur Model | Akurasi (%) (*Mean ± Std*) | Macro F1 (*Mean ± Std*) | Presisi Makro | Recall Makro | Jumlah Parameter | Ukuran TFLite (MB) | Latensi CPU (ms) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **MobileNetV3Large** | **97.22% ± 4.03%** | 0.9698 ± 0.0435 | 0.9782 | 0.9679 | **3,243,396** | **12.30 MB** | **11.40 ms** |
| **2** | **EfficientNetV2S** | **97.22% ± 2.59%** | 0.9692 ± 0.0301 | 0.9757 | 0.9688 | 20,660,324 | 78.12 MB | 83.70 ms |
| **3** | **EfficientNetB0** | 97.19% ± 3.44% | **0.9714 ± 0.0351** | **0.9782** | **0.9690** | 4,378,535 | 16.56 MB | 19.31 ms |
| **4** | **ConvNeXtTiny** | 97.19% ± 3.44% | **0.9714 ± 0.0350** | 0.9773 | **0.9690** | 28,018,020 | 106.96 MB | 206.05 ms |
| **5** | **MobileNetV2** | 95.81% ± 4.06% | 0.9570 ± 0.0425 | 0.9674 | 0.9545 | **2,586,948** | **9.72 MB** | 12.84 ms |
| **6** | **ResNet50** | 95.81% ± 3.42% | 0.9587 ± 0.0337 | 0.9666 | 0.9557 | 24,113,284 | 91.63 MB | 103.29 ms |

*Catatan: Nilai metrik diperoleh dari rerata 5 lipatan data uji Stratified 5-Fold CV. Latensi diukur pada CPU multi-core (rerata 100 iterasi).*

Berdasarkan data pada Tabel 1, terungkap beberapa temuan empiris utama:
1. **Keseimbangan Puncak Akurasi:** Tiga model teratas (MobileNetV3Large, EfficientNetV2S, dan EfficientNetB0) mencapai rentang akurasi yang sangat kompetitif ($97.19\% - 97.22\%$). EfficientNetV2S mencatatkan deviasi standar terendah ($\pm 2.59\%$), mengindikasikan kestabilan generalisasi lintas lipatan yang sangat konsisten.
2. **Disparitas Efisiensi Ekstrem:** Kendati MobileNetV3Large dan EfficientNetV2S membukukan akurasi identik ($97.22\%$), MobileNetV3Large memiliki kecepatan inferensi **7.34 kali lebih cepat** ($11.40\text{ ms}$ vs $83.70\text{ ms}$) dan ukuran berkas **6.35 kali lebih hemat** ($12.30\text{ MB}$ vs $78.12\text{ MB}$).
3. **Anomali Kapasitas Parameter Raksasa:** Arsitektur berparameter besar seperti ConvNeXtTiny (28.02M parameter) dan ResNet50 (24.11M parameter) terbukti tidak memberikan keunggulan akurasi dibandingkan arsitektur ringan 3M-4M parameter. ResNet50 bahkan menempati peringkat terbawah bersama MobileNetV2 dengan akurasi $95.81\%$.

### 3.2 Analisis Dinamika Pelatihan Dua Fase (*Transfer Learning Dynamics*)
Perbandingan performa antara Fase 1 (*Frozen Feature Extraction*) dan Fase 2 (*Fine-Tuning*) dirangkum pada Tabel 2.

#### Tabel 2. Komparasi Akurasi Antara Fase 1 dan Fase 2

| Arsitektur Model | Akurasi Fase 1 (%) | Akurasi Fase 2 (%) | Selisih ($\Delta$) | Analisis Dinamika Pembelajaran |
| :--- | :---: | :---: | :---: | :--- |
| **MobileNetV3Large** | 97.22% | 97.22% | $+0.00\%$ | Representasi fitur awal ImageNet telah menangkap pola spasial secara optimal; konvergensi stabil. |
| **MobileNetV2** | 93.74% | 95.81% | $+2.07\%$ | Adaptasi domain berhasil mentransfer bobot lapis atas ke pola fenotipe sapi. |
| **EfficientNetB0** | 97.19% | 97.19% | $+0.00\%$ | Skalasi kompon menjaga kestabilan representasi fitur tanpa pergeseran bobot berlebih. |
| **EfficientNetV2S** | 97.91% | 97.22% | $-0.69\%$ | Terjadi pergeseran representasi minor (*mild representational drift*) pada dataset berukuran terbatas. |
| **ConvNeXtTiny** | 95.05% | 97.19% | $+2.14\%$ | Kernel konvolusi besar $7\times 7$ memerlukan penyesuaian lapis atas untuk mempelajari tekstur bulu ternak. |
| **ResNet50** | 96.50% | 95.81% | $-0.69\%$ | Kapasitas lapisan residual yang terlalu masif memicu sedikit fluktuasi pada data validasi kecil. |

Hasil pada Tabel 2 menegaskan bahwa pada arsitektur yang dirancang dengan mekanisme atensi kanal (*Squeeze-and-Excitation*) seperti MobileNetV3Large dan EfficientNetB0, representasi fitur spasial umum telah sangat representatif sejak Fase 1, menghasilkan kestabilan tinggi tanpa rentan degradasi bobot saat *fine-tuning*.

### 3.3 Analisis Kinerja Per-Kelas Ras Sapi
Kinerja klasifikasi pada masing-masing ras sapi dievaluasi melalui metrik Presisi, Recall, dan F1-Score yang disajikan pada Tabel 3.

#### Tabel 3. Rincian Metrik Per-Kelas Ras Sapi pada Fase Fine-Tuning

| Arsitektur Model | Sapi Bali (F1) | Sapi Brahman (F1) | Sapi Brangus (F1) | Sapi Limusin (F1) | Macro F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MobileNetV3Large** | 0.9664 | 0.9467 | 0.9882 | 0.9778 | **0.9698** |
| **MobileNetV2** | 0.9664 | 0.9181 | **1.0000** | 0.9433 | 0.9570 |
| **EfficientNetB0** | 0.9664 | **0.9664** | 0.9867 | 0.9660 | **0.9714** |
| **EfficientNetV2S** | 0.9552 | 0.9600 | 0.9749 | **0.9867** | 0.9692 |
| **ConvNeXtTiny** | 0.9664 | 0.9532 | **1.0000** | 0.9660 | **0.9714** |
| **ResNet50** | 0.9379 | 0.9664 | **1.0000** | 0.9306 | 0.9587 |

Evaluasi per-kelas menunjukkan korelasi erat dengan karakteristik morfologis biologis:
- **Sapi Brangus** mencatatkan F1-Score tertinggi (0.9749 hingga 1.0000) pada seluruh arsitektur. Warna bulu hitam pekat tanpa tanduk memberikan tanda visual khas yang sangat mudah dipisahkan oleh filter konvolusi.
- **Sapi Bali** mencapai F1-Score konsisten 0.9664 pada mayoritas model. Keberadaan cermin pantat putih (*white rump*) dan kaos kaki putih berfungsi sebagai pembeda kuat dari ras lainnya.
- **Sapi Brahman** membukukan F1-Score antara 0.9181 hingga 0.9664. Punuk dan gelambir leher terdeteksi dengan baik pada tampak samping, namun sedikit mengalami penurunan akurasi pada sudut pemotretan langsung dari belakang.
- **Sapi Limusin** memperoleh F1-Score 0.9306 hingga 0.9867. Kesalahan klasifikasi minor terjadi pada individu sapi muda yang mengalami kemiripan gradasi warna bulu cokelat dengan sapi betina ras lain pada kondisi pencahayaan terik.

### 3.4 Pembuktian Signifikansi Statistik: Uji McNemar dan Prinsip Occam's Razor
Tabel 4 menyajikan matriks nilai signifikansi statistik ($p$-value) dari pengujian berpasangan *Pairwise McNemar's Test* antar keenam arsitektur.

#### Tabel 4. Matriks Signifikansi Statistik Pairwise McNemar's Test ($p$-value)

| Pasangan Model (A vs B) | Kasus Diskordan $b$ | Kasus Diskordan $c$ | McNemar $p$-value | Signifikan pada $\alpha = 0.05$? |
| :--- | :---: | :---: | :---: | :---: |
| MobileNetV3Large vs MobileNetV2 | 2 | 0 | 0.5000 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV3Large vs EfficientNetB0 | 1 | 1 | 1.0000 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV3Large vs EfficientNetV2S | 1 | 1 | 1.0000 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV3Large vs ConvNeXtTiny | 1 | 1 | 1.0000 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV3Large vs ResNet50 | 4 | 2 | 0.6875 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV2 vs EfficientNetB0 | 0 | 2 | 0.5000 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV2 vs EfficientNetV2S | 0 | 2 | 0.5000 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV2 vs ConvNeXtTiny | 0 | 2 | 0.5000 | **Tidak Signifikan ($p \ge 0.05$)** |
| MobileNetV2 vs ResNet50 | 3 | 3 | 1.0000 | **Tidak Signifikan ($p \ge 0.05$)** |
| EfficientNetB0 vs EfficientNetV2S | 2 | 2 | 1.0000 | **Tidak Signifikan ($p \ge 0.05$)** |
| EfficientNetB0 vs ConvNeXtTiny | 1 | 1 | 1.0000 | **Tidak Signifikan ($p \ge 0.05$)** |
| EfficientNetB0 vs ResNet50 | 4 | 2 | 0.6875 | **Tidak Signifikan ($p \ge 0.05$)** |
| EfficientNetV2S vs ConvNeXtTiny | 2 | 2 | 1.0000 | **Tidak Signifikan ($p \ge 0.05$)** |
| EfficientNetV2S vs ResNet50 | 5 | 3 | 0.7266 | **Tidak Signifikan ($p \ge 0.05$)** |
| ConvNeXtTiny vs ResNet50 | 3 | 1 | 0.6250 | **Tidak Signifikan ($p \ge 0.05$)** |

Seluruh perbandingan berpasangan menghasilkan nilai $p \ge 0.5000$, jauh melampaui ambang batas signifikansi $\alpha = 0.05$. Hal ini membuktikan secara empiris bahwa penambahan kompleksitas komputasi hingga 28 juta parameter (ConvNeXtTiny) tidak memberikan peningkatan akurasi yang nyata secara saintifik dibandingkan model 3.2 juta parameter (MobileNetV3Large). Temuan ini menegakkan prinsip epistemologis **Occam's Razor**: dalam ketiadaan bukti keunggulan statistik yang signifikan, model dengan kompleksitas parameter terendah wajib dipilih demi meminimalkan beban komputasi dan risiko *overfitting*.

### 3.5 Validasi Interpretabilitas Visual Berbasis Grad-CAM
Visualisasi Grad-CAM pada lapisan konvolusi terakhir membuktikan bahwa representasi fitur model berkorelasi langsung dengan ciri morfologi anatomi ternak:
1. Pada **Sapi Brahman**, aktivasi puncak terlokalisasi kuat pada punuk (*hump*) dan gelambir leher (*dewlap*).
2. Pada **Sapi Bali**, atensi visual terpusat pada kontur kepala/telinga tegak dan area cermin pantat putih.
3. Pada **Sapi Limusin**, peta panas mengunci area punggung berotot padat dan profil paha karkas.
4. Pada **Sapi Brangus**, aktivasi tersebar merata di sepanjang torso silindris hitam dan ketiadaan tanduk.

Peta aktivasi menunjukkan intensitas mendekati nol pada elemen latar belakang kandang (palung pakan semen, jerami kering, dan pagar bambu), membuktikan bahwa model terbebas dari bias korelasi semu lingkungan (*Clever Hans Effect*).

### 3.6 Kelayakan Komputasi Tepi (*Edge Deployment for SapiKenal*)
Analisis *trade-off* antara akurasi, ukuran berkas instalasi, dan latensi CPU membuktikan bahwa **MobileNetV3Large** menempati titik optimal (*Pareto frontier*):
- **Ukuran Berkas:** Berkas TFLite FP32 MobileNetV3Large hanya berukuran **12.30 MB**, 6.35 kali lebih ringkas dibandingkan EfficientNetV2S (78.12 MB) dan 8.70 kali lebih hemat dibanding ConvNeXtTiny (106.96 MB). Ukuran yang sangat ringkas ini memungkinkan aplikasi Android *SapiKenal* diunduh dan dipasang secara cepat tanpa membebani memori internal ponsel pintar peternak.
- **Latensi Inferensi CPU:** Dengan latensi eksekusi hanya **11.40 ms**, proses inferensi berlangsung seketika (*real-time*, ~87 frame per detik), 7.3 kali lebih cepat dibanding EfficientNetV2S (83.70 ms) dan 18 kali lebih cepat dibanding ConvNeXtTiny (206.05 ms).
- **Kesiapan TKT 5:** Efisiensi komputasi ini menjamin aplikasi mobile dapat menjalankan inferensi klasifikasi citra secara mandiri (*offline-first*) di dalam kandang tanpa jaringan internet, mendukung pencapaian Tingkat Kesiapterapan Teknologi TKT 5 pada purwarupa sistem informasi peternakan terpadu.

---

## 4. KESIMPULAN

Studi komparasi terhadap enam arsitektur CNN modern dalam klasifikasi empat ras sapi representatif di Kabupaten Boyolali membuktikan bahwa **MobileNetV3Large** merupakan arsitektur Pareto-optimal terbaik. Model ini mencatatkan akurasi **97.22% ± 4.03%** dan Macro F1-Score **0.9698 ± 0.0435**, setara dengan model berbobot raksasa EfficientNetV2S (97.22%) dan melampaui ResNet50 (95.81%). Hasil uji statistik non-parametrik *Pairwise McNemar's Test* ($p \ge 0.5000$) secara formal melegitimasi prinsip *Occam's Razor* bahwa penambahan parameter hingga 28 juta tidak memberikan keunggulan performa yang signifikan. Analisis Grad-CAM mengonfirmasi bahwa model mengambil keputusan berdasarkan karakteristik biologis morfologis ras sapi tanpa terdistorsi bias latar belakang kandang. Pada format komputasi tepi *TensorFlow Lite FP32*, MobileNetV3Large membutuhkan ruang penyimpanan hanya **12.30 MB** dengan latensi CPU **11.40 ms**, menjadikannya mesin inferensi yang sangat ideal untuk diintegrasikan secara luring (*offline-first*) ke dalam aplikasi mobile sistem informasi peternakan **SapiKenal** (TKT 5). 

Arah penelitian berikutnya meliputi ekspansi pengumpulan dataset lapangan ke enam ras sapi Boyolali secara penuh (dengan mengintegrasikan Sapi Jawa/PO dan Sapi Madura), penerapan teknik kuantisasi bilangan bulat 8-bit (*INT8 Post-Training Quantization*) untuk memangkas ukuran model menjadi ~3 MB dengan latensi <6 ms, serta integrasi modul deteksi objek ringan (*bounding-box crop*) untuk meningkatkan ketahanan identifikasi pada kondisi kandang padat multi-sapi.

---

## DAFTAR PUSTAKA

[1] Pemerintah Provinsi Jawa Tengah, "Peluang Investasi Komoditas Peternakan Kabupaten Boyolali," *Central Java Investment Platform (CJIP)*, 2023. [Daring]. Tersedia: [https://cjip.jatengprov.go.id](https://cjip.jatengprov.go.id).  
[2] Dinas Peternakan dan Perikanan Kabupaten Boyolali, *Buku Saku Statistik Peternakan dan Kesehatan Hewan Kabupaten Boyolali Tahun 2024*, Boyolali: Disnakkan Kabupaten Boyolali, 2024.  
[3] B. Li, J. Fang, and Y. Zhao, "RTDETR-Refa: A real-time detection method for multi-breed classification of cattle," *Journal of Real-Time Image Processing*, vol. 22, no. 1, art. no. 38, pp. 1–16, 2025, doi: 10.1007/s11554-024-01613-7.  
[4] J. Sathya and V. Asha, "Deep Learning-based Computer Vision System for Multi-Class Cow Breed Classification using Convolutional Neural Networks," in *Proceedings of the 2026 International Conference on Computer Networks and Inventive Communication Technologies (ICCNCT)*, 2026, pp. 1–6, doi: 10.1109/ICCNCT68477.2026.11590145.  
[5] R. J. Mathews and A. Misra, "MicroBreedNet: A Densely Connected Hybrid Framework for Fine-Grained Identification of the Vechur Cattle Breed," in *Proceedings of the 4th International Conference on Applied Artificial Intelligence and Computing (ICAAIC)*, 2025, pp. 1–8, doi: 10.1109/ICAAIC64647.2025.11330436.  
[6] M. E. Hossain, M. A. Kabir, L. Zheng, D. L. Swain, S. McGrath, and J. Medway, "A systematic review of machine learning techniques for cattle identification: Datasets, methods and future directions," *Artificial Intelligence in Agriculture*, vol. 6, pp. 138–155, 2022, doi: 10.1016/j.aiia.2022.09.002.  
[7] A. R. Manga’, Herawati, and Purnawansyah, "Utilization of Deep Learning YOLO V9 for Identification and Classification of Toraja Buffalo Breeds," *ILKOM Jurnal Ilmiah*, vol. 17, no. 1, pp. 12–19, 2025, doi: 10.33096/ilkom.v17i1.2349.12-19.  
[8] W. Andrew, J. Gao, S. Mullan, N. Campbell, A. W. Dowsey, and T. Burghardt, "Visual identification of individual Holstein-Friesian cattle via deep metric learning," *Computers and Electronics in Agriculture*, vol. 185, art. no. 106133, pp. 1–13, 2021, doi: 10.1016/j.compag.2021.106133.  
[9] A. B, B. N. S. Kumar, and A. S, "BharatPashu: Lightweight EfficientNet Architecture for Indigenous Indian Cattle and Buffalo Breed Classification on Mobile Devices," in *Proceedings of the 2nd International Conference on Computing for Sustainability and Intelligent Future (COMP-SIF)*, 2026, pp. 1–6, doi: 10.1109/COMP-SIF69752.2026.11481891.  
[10] Y. Qiao, H. Kong, C. Clark, S. Lomax, D. Su, S. Eiffert, and S. Sukkarieh, "Intelligent perception for cattle monitoring: A review for cattle identification, body condition score evaluation, and weight estimation," *Computers and Electronics in Agriculture*, vol. 185, art. no. 106143, pp. 1–17, 2021, doi: 10.1016/j.compag.2021.106143.  
[11] P. D. Pathak and S. Prakash, "Enhancing digital cattle identification with fine-grained image analysis," *Expert Systems with Applications*, vol. 297, art. no. 129409, pp. 1–16, 2026, doi: 10.1016/j.eswa.2025.129409.  
[12] S. Sahu and A. Khanna, "A Hybrid Convolution–Transformer Attention Framework for Precise Fine-Grained Cattle Breed Classification," in *Proceedings of the 5th International Conference on Power, Control and Computing Technologies (ICPC2T)*, 2026, pp. 1–6, doi: 10.1109/ICPC2T68221.2026.11646362.  
[13] S. Jain, A. Laad, and M. Patidar, "An Explainable Deep Learning Framework for Efficient Cattle Breed Identification Using ResNet-50," in *Proceedings of the IEEE Madhya Pradesh Section Conference (MPCON)*, 2026, pp. 1–6, doi: 10.1109/MPCON69668.2026.11508566.  
[14] A. Yılmaz and G. N. Uzun, "Detection and Breed Classification of Cattle Using YOLO v4 Algorithm," in *Proceedings of the 2021 International Conference on INnovations in Intelligent SysTems and Applications (INISTA)*, 2021, pp. 1–6, doi: 10.1109/INISTA52262.2021.9548440.  
[15] F. V. J. S. Marshal and Kishore A, "Cattle Breed identification using EfficientNet and Transfer Learning," in *Proceedings of the 2026 International Conference on Intelligent Computing (ICONIC)*, 2026, pp. 1–6, doi: 10.1109/ICONIC67661.2026.11517884.  
[16] M. Luthra, M. Sharma, and P. Chaudhary, "Cattle Identification and Detection using Vision Transformers and YOLOv8," *Journal of Information Systems Engineering and Management*, vol. 10, no. 42s, pp. 1–10, 2025, doi: 10.55267/iadt.07.15182.  
[17] A. Howard, M. Sandler, G. Chu, L. C. Chen, B. Chen, M. Tan, W. Wang, Y. Zhu, R. Pang, V. Vasudevan, Q. V. Le, and H. Adam, "Searching for MobileNetV3," in *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*, 2019, pp. 1314–1324, doi: 10.1109/ICCV.2019.00140.  
[18] M. Sandler, A. Howard, M. Zhu, A. Zhmoginov, and L. C. Chen, "MobileNetV2: Inverted Residuals and Linear Bottlenecks," in *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2018, pp. 4510–4520, doi: 10.1109/CVPR.2018.00474.  
[19] M. Tan and Q. V. Le, "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks," in *Proceedings of the 36th International Conference on Machine Learning (ICML)*, 2019, pp. 6105–6114.  
[20] M. Tan and Q. V. Le, "EfficientNetV2: Smaller Models and Faster Training," in *Proceedings of the 38th International Conference on Machine Learning (ICML)*, 2021, pp. 10096–10106.  
[21] Z. Liu, H. Mao, C. Y. Wu, C. Feichtenhofer, T. Darrell, and S. Xie, "A ConvNet for the 2020s," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 2022, pp. 11976–11986, doi: 10.1109/CVPR52688.2022.01167.  
[22] K. He, X. Zhang, S. Ren, and J. Sun, "Deep Residual Learning for Image Recognition," in *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 770–778, doi: 10.1109/CVPR.2016.90.  
[23] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, "Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization," *International Journal of Computer Vision*, vol. 128, no. 2, pp. 336–359, 2020, doi: 10.1007/s11263-019-01228-3.
[24] Encyclopaedia Britannica, "Information system | Definition, Examples, & Facts," updated Feb. 27, 2026. [Daring]. Tersedia: [https://www.britannica.com/topic/information-system](https://www.britannica.com/topic/information-system).  
[25] N. A. Saputra, D. A. Nugroho, A. N. Hidayanto, dkk., "A Systematic Review for Classification and Selection of Deep Learning Methods," *Array*, vol. 22, art. no. 100341, pp. 1–15, 2024, doi: 10.1016/j.array.2024.100341.  
[26] M. S. Mahmud, L. Abdelgawad, S. M. M. K. Hossain, dkk., "A systematic literature review on deep learning applications for precision cattle farming," *Computers and Electronics in Agriculture*, vol. 180, art. no. 105887, pp. 1–18, 2021, doi: 10.1016/j.compag.2020.105887.  
[27] F. de Lima Weber, V. A. de Moraes Weber, G. V. Menezes, dkk., "Recognition of Pantaneira cattle breed using computer vision and convolutional neural networks," *Computers and Electronics in Agriculture*, vol. 175, art. no. 105548, pp. 1–12, 2020, doi: 10.1016/j.compag.2020.105548.  
[28] Z. Weng, F. Meng, S. Liu, Y. Zhang, Z. Zheng, dan C. Gong, "Cattle face recognition based on a Two-Branch convolutional neural network," *Computers and Electronics in Agriculture*, vol. 196, art. no. 106871, pp. 1–11, 2022, doi: 10.1016/j.compag.2022.106871.
