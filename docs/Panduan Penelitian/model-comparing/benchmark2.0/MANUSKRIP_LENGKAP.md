# BAB I: PENDAHULUAN

## Latar Belakang, Tinjauan Permasalahan, dan Kebaruan Penelitian

---

## 1.1 Latar Belakang dan Urgensi Masalah

Sektor peternakan sapi memegang peranan krusial dalam memperkuat ketahanan pangan hewani nasional dan menopang perekonomian masyarakat pedesaan di Indonesia. Kabupaten Boyolali, Provinsi Jawa Tengah, secara luas diakui sebagai salah satu lumbung dan sentra peternakan sapi terkemuka di Pulau Jawa. Populasi sapi di wilayah ini mencakup puluhan ribu ekor yang tersebar di sentra peternakan rakyat dan pasar-pasar hewan regional, mencakup sapi perah maupun sapi potong unggulan.

Setiap ras atau jenis sapi memiliki karakteristik fenotipik, fisiologis, dan produktivitas yang berbeda secara signifikan. Di tingkat nasional maupun di Kabupaten Boyolali, terdapat enam ras sapi yang menjadi fokus strategis dalam tata kelola peternakan, mencakup ras lokal adaptif (Sapi Jawa/PO, Sapi Madura, dan Sapi Bali) serta ras potong introduksi unggulan berdaya hasil tinggi (Sapi Brahman, Sapi Brangus, dan Sapi Limusin). Karakteristik biologis masing-masing ras mencakup:

- **Sapi Bali** (*Bos javanicus domesticus*) dikenal memiliki persentase karkas tinggi, daya adaptasi tinggi terhadap pakan berserat kasar, serta tingkat fertilitas yang luar biasa.
- **Sapi Brahman** (*Bos indicus*) memiliki ketahanan tinggi terhadap paparan panas tropis dan ektoparasit berkat keberadaan punuk (*hump*) dan gelambir leher (*dewlap*) yang luas.
- **Sapi Brangus** (persilangan Brahman × Aberdeen Angus) menggabungkan keunggulan ketahanan iklim tropis dengan laju pertambahan bobot badan harian (*Average Daily Gain* / ADG) yang pesat serta kualitas daging tanpa lemak.
- **Sapi Limusin** (*Bos taurus*) merupakan ras tipe besar asal Eropa dengan pertumbuhan otot yang sangat cepat dan hasil karkas daging bernilai ekonomis tinggi.
- **Sapi Jawa (Peranakan Ongole / PO)** dan **Sapi Madura** yang menjadi penopang utama peternakan rakyat berkat daya tahan luar biasa terhadap iklim lokal dan efisiensi pemanfaatan pakan berserat.

Perbedaan biologis dan genetik ini secara langsung menentukan **strategi pemeliharaan, formulasi ransum pakan, manajemen penggemukan, hingga penaksiran harga jual ternak di pasar hewan**. Kesalahan dalam mengidentifikasi jenis sapi dapat menimbulkan dampak berantai, antara lain kerugian finansial akibat kekeliruan taksiran bobot karkas, ketidakefektifan formulasi nutrisi pakan, hingga terhambatnya program pemuliaan genetik (*genetic breeding*) untuk menghasilkan bibit ternak unggul.

---

## 1.2 Permasalahan Identifikasi Konvensional

Meskipun klasifikasi jenis sapi memiliki nilai ekonomis yang sangat strategis, praktik identifikasi di tingkat peternak rakyat dan pasar hewan tradisional saat ini masih mengandalkan **pengamatan visual konvensional secara subjektif**. Para peternak dan pedagang hewan umumnya mengenali sapi hanya berdasarkan pengamatan sekilas terhadap bentuk punuk, warna bulu, lipatan gelambir, atau postur tubuh ternak.

Metode konvensional ini memiliki sejumlah kelemahan mendasar:

1. **Tingginya Subjektivitas dan Bias Pengamat:** Identifikasi sangat bergantung pada pengalaman empiris perorangan yang sulit distandardisasi. Peternak pemula atau penyuluh peternakan seringkali kesulitan membedakan ras murni dengan ras hasil persilangan silang (*crossbreed*) yang memiliki kemiripan morfologis fenotipik.
2. **Kemiripan Ciri Fenotipe Antar-Ras:** Pada kondisi tertentu seperti masa pertumbuhan sapi muda atau sapi betina, gradasi warna bulu dan struktur postur antara Sapi Bali betina dengan Sapi Limusin muda menunjukkan kemiripan visual yang rentan memicu misklasifikasi.
3. **Ketiadaan Rekam Jejak Digital yang Objektif:** Tidak adanya sistem pencatatan berbasis citra digital menyebabkan data persebaran populasi ternak dan transaksi jual beli di sentra peternakan Boyolali sulit divalidasi secara saintifik.

---

## 1.3 Peluang Pembelajaran Mendalam (*Deep Learning*), Sistem Informasi, dan Tantangan Komputasi Tepi (*Edge Computing*)

Perkembangan teknologi visi komputer (*computer vision*) berbasis pembelajaran mendalam (*deep learning*), khususnya arsitektur Convolutional Neural Network (CNN), menawarkan peluang besar untuk mentransformasi identifikasi jenis sapi menjadi proses komputasi yang objektif, otomatis, dan akurat. Di sisi lain, kemajuan rekayasa perangkat lunak memungkinkan pengintegrasian model kecerdasan buatan tersebut ke dalam **sistem informasi terpadu (berbasis web dan aplikasi bergerak / mobile)** yang dapat memfasilitasi pencatatan digital populasi ternak, validasi transaksi di pasar hewan, serta diseminasi informasi bagi peternak dan penyuluh di lapangan.

Kendati demikian, penerapan modul inferensi *deep learning* ke dalam sistem informasi pada skenario nyata peternakan rakyat di pedesaan Boyolali menghadapi **kendala infrastruktur dan komputasi yang nyata**:

1. **Keterbatasan Konektivitas Jaringan Internet:** Mayoritas kandang peternakan dan pasar hewan di pedesaan Boyolali berada pada area dengan sinyal internet yang tidak stabil atau bahkan tanpa jangkauan jaringan (*blind spot*). Situasi ini menuntut subsistem bergerak (*mobile*) yang mengusung paradigma **luring mandiri (*offline-first*)**, di mana inferensi klasifikasi citra harus dieksekusi secara lokal pada perangkat bergerak (*mobile device*).
2. **Keterbatasan Sumber Daya Perangkat Seluler:** Mayoritas peternak menggunakan ponsel pintar berspesifikasi menengah ke bawah (*low-to-mid range Android devices*) dengan kapasitas memori RAM terbatas dan tanpa akselerator grafis (GPU) khusus.
3. **Dilema Trade-off Akurasi vs Efisiensi:** Model berkapasitas besar (seperti ResNet50 atau varian Vision Transformer) memang dikenal memiliki akurasi tinggi pada server komputasi awan. Namun, model berbobot puluhan juta parameter tersebut menghasilkan ukuran berkas instalasi yang sangat besar ($>90\text{ MB}$) dan latensi inferensi CPU yang tinggi ($>100\text{ ms}$), yang dapat menyebabkan *freeze*, konsumsi baterai boros, dan kegagalan responsivitas aplikasi di lapangan.

Oleh karena itu, diperlukan penyelidikan ilmiah yang ketat untuk menemukan arsitektur *deep learning* yang menempati titik keseimbangan optimal (*Pareto frontier / sweet spot*): **memiliki akurasi klasifikasi prima sekaligus berukuran ringkas dan berlatensi sangat rendah pada komputasi tepi CPU**, sebagai mesin inferensi inti (*core engine*) bagi sistem informasi peternakan yang andal.

---

## 1.4 Tinjauan Studi Terdahulu dan Kesenjangan Penelitian (*Research Gap*)

Pemanfaatan visi komputer dalam sektor peternakan cerdas (*precision livestock farming*) telah menjadi topik penelitian aktif dalam beberapa tahun terakhir:

- **Identifikasi Individual dan Wajah Sapi:** Qiao dkk. (2020) mengembangkan kerangka kerja kombinasi CNN dan LSTM untuk identifikasi sapi secara individual berdasarkan urutan video. Weng dkk. (2022) mengusulkan model *Two-Branch CNN* untuk pengenalan wajah sapi perah. Namun, penelitian-penelitian tersebut berfokus pada pengenalan individu (*individual biometric tracking*) pada peternakan modern berskala industri dengan setup kamera statis, bukan pada klasifikasi jenis/ras sapi di peternakan rakyat.
- **Klasifikasi Ras Ternak:** de Lima Weber dkk. (2020) menguji model CNN untuk mengenali ras sapi Pantaneira dari berbagai sudut pemotretan. Studi BharatPashu di India (2024) mengevaluasi model EfficientNet-B3 untuk identifikasi ras sapi Zebu dengan akurasi 82.55%. Di Indonesia, beberapa penelitian awal telah menguji MobileNetV2 dan ResNet50 untuk ras lokal, namun umumnya hanya menggunakan pembagian data tunggal (*single split*) pada dataset yang sangat kecil tanpa validasi statistik silang (*k-fold cross-validation*).

Berdasarkan tinjauan literatur di atas, teridentifikasi sejumlah **kesenjangan penelitian (*research gaps*)** yang belum terjawab:

1. **Ketiadaan Komparasi Lintas Paradigma Arsitektur yang Komprehensif:** Belum ada studi komparatif sistematis yang membandingkan arsitektur CNN ringan berbasis Neural Architecture Search (*MobileNetV3Large*), arsitektur skala kompon (*EfficientNetB0, EfficientNetV2S*), arsitektur residual klasik (*ResNet50*), dan arsitektur konvolusi modern berdesain Vision Transformer (*ConvNeXtTiny*) secara setara (*controlled protocol*) pada domain klasifikasi ras sapi Indonesia.
2. **Kurangnya Uji Signifikansi Statistik Formal:** Sebagian besar literatur sebelumnya mengklaim suatu model "lebih baik" hanya berdasarkan selisih persentase akurasi nominal, tanpa melakukan pengujian signifikansi statistik formal (seperti uji McNemar) untuk membuktikan apakah peningkatan tersebut nyata secara ilmiah atau sekadar fluktuasi acak.
3. **Ancaman Bias Latar Belakang (*Clever Hans Effect*):** Belum banyak penelitian klasifikasi ternak lokal yang menyertakan analisis *Explainable AI* (XAI) berbasis Grad-CAM untuk membuktikan bahwa model benar-benar membedakan sapi berdasarkan fitur anatomi morfologis biologis, bukan mengeksploitasi bias visual latar belakang kandang, rumput, atau pagar.
4. **Ketiadaan Profiling Deployment Riil:** Jarang ditemukan penelitian akademik yang mengukur metrik inferensi riil pada format komputasi tepi (TensorFlow Lite FP32) dan latensi CPU per-milidetik sebagai acuan implementasi aplikasi mobile peternak di lapangan.

---

## 1.5 Kebaruan dan Kontribusi Penelitian (*Novelty &amp; Contributions*)

Untuk menjembatani kesenjangan penelitian tersebut dan mendukung pengembangan arsitektur sistem informasi peternakan terpadu (berbasis web dan aplikasi mobile **SapiKenal**) pada tingkat kesiapterapan teknologi **TKT 5**, penelitian ini memposisikan diri sebagai riset penentu mesin inferensi cerdas (*core intelligent engine selection*). Dalam peta jalan (*roadmap*) jangka panjang penelitian yang menargetkan enam jenis sapi di Kabupaten Boyolali (Sapi Jawa, Madura, Bali, Brahman, Brangus, dan Limusin), studi komparasi model pada tahap ini difokuskan pada **empat ras representatif dengan disparitas morfologi fenotipik paling kontras** (Bali, Brahman, Brangus, dan Limusin) sebagai tolok ukur ketahanan representasi visual arsitektur CNN sebelum ekspansi ke ras lokal Jawa dan Madura. Penelitian ini menyajikan empat kontribusi ilmiah utama:

> 📊 **Berkas Diagram Vektor Draw.io:** [`assets/kebaruan_penelitian.drawio`](./assets/kebaruan_penelitian.drawio)

1. **Komparasi Multi-Arsitektur Multi-Paradigma:** Melakukan studi komparatif terstandarisasi terhadap enam arsitektur CNN terkemuka (MobileNetV3Large, MobileNetV2, EfficientNetB0, EfficientNetV2S, ConvNeXtTiny, dan ResNet50) menggunakan protokol pelatihan dua fase (*feature extraction* dan *fine-tuning* terkalibrasi) pada citra ras sapi unggulan di Boyolali untuk menetapkan arsitektur terbaik bagi modul sistem informasi.
2. **Validasi Reliabilitas dengan Stratified 5-Fold Cross-Validation:** Menjamin seluruh 143 citra terkurasi dievaluasi secara independen tanpa risiko *sampling bias*, dengan pelaporan metrik *Mean ± Std* serta metrik per-kelas yang presisi pada empat ras pembeda utama.
3. **Penerapan Uji Signifikansi McNemar:** Memberikan landasan statistik empiris bahwa model berbobot puluhan juta parameter tidak memiliki keunggulan performa yang signifikan ($p > 0.05$) dibanding model ringan, sehingga menegakkan prinsip keilmuan *Occam's Razor* dalam pemilihan model produksi sistem informasi.
4. **Validasi Morfologis XAI dan Kesiapan Edge AI (TKT 5):** Menyajikan visualisasi Grad-CAM untuk membuktikan model mengunci atensi pada ciri anatomi khas ras (punuk Brahman, moncong Bali, otot Brangus, profil Limusin) sekaligus membuktikan kelayakan inferensi *real-time* ($11.40\text{ ms}$) dan ukuran hemat ($12.30\text{ MB}$) untuk integrasi aplikasi mobile *SapiKenal* secara luring (*offline-first*) maupun backend web sistem informasi.

---

## 1.6 Tujuan Penelitian

Sesuai dengan rumusan masalah dan roadmap penelitian hibah PUP Polines, tujuan penelitian ini adalah:

1. Menganalisis dan membandingkan performa klasifikasi citra dari enam arsitektur CNN modern dalam mengidentifikasi empat ras sapi unggulan representatif (Bali, Brahman, Brangus, dan Limusin) sebagai basis pemilihan model cerdas terbaik bagi sistem informasi peternakan Boyolali.
2. Membuktikan secara statistik menggunakan uji McNemar apakah penambahan parameter model menghasilkan perbedaan performa klasifikasi yang signifikan secara saintifik.
3. Menginterpretasikan representasi visual model terbaik menggunakan Grad-CAM guna memverifikasi keterkaitan atensi fitur dengan morfologi biologis ternak dan ketiadaan bias latar belakang kandang.
4. Mengukur efisiensi komputasi tepi (ukuran berkas TFLite dan latensi inferensi CPU) untuk menetapkan arsitektur terbaik yang siap dideploy pada aplikasi mobile peternak *SapiKenal* maupun diintegrasikan ke sistem informasi berbasis web.

---

## 3. HASIL DAN PEMBAHASAN

### 3.1 Performa Komparatif 6 Arsitektur CNN

Tabel 1.1 merangkum performa klasifikasi akhir seluruh arsitektur setelah menyelesaikan Fase 2 (*Fine-Tuning*) pada skema 5-fold cross-validation.

#### Tabel 1.1 Master Komparasi Performa Klasifikasi dan Efisiensi Deployment Komputasi Tepi


| Peringkat | Arsitektur Model     | Akurasi (%) (*Mean ± Std*) | Macro F1 (*Mean ± Std*) | Presisi Makro | Recall Makro | Jumlah Parameter | Ukuran TFLite (MB) | Latensi CPU (ms) |
| :---------: | -------------------- | :--------------------------: | :-----------------------: | :-------------: | :------------: | :----------------: | :------------------: | :----------------: |
| 1         | **MobileNetV3Large** | **97.22% ± 4.03%**         | 0.9698 ± 0.0435         | 0.9782        | 0.9679       | **3,243,396**    | **12.30 MB**       | **11.40 ms**     |
| 2         | **EfficientNetV2S**  | **97.22% ± 2.59%**         | 0.9692 ± 0.0301         | 0.9757        | 0.9688       | 20,660,324       | 78.12 MB           | 83.70 ms         |
| 3         | **EfficientNetB0**   | 97.19% ± 3.44%             | **0.9714 ± 0.0351**     | **0.9782**    | **0.9690**   | 4,378,535        | 16.56 MB           | 19.31 ms         |
| 4         | **ConvNeXtTiny**     | 97.19% ± 3.44%             | **0.9714 ± 0.0350**     | 0.9773        | **0.9690**   | 28,018,020       | 106.96 MB          | 206.05 ms        |
| 5         | **MobileNetV2**      | 95.81% ± 4.06%             | 0.9570 ± 0.0425         | 0.9674        | 0.9545       | **2,586,948**    | **9.72 MB**        | 12.84 ms         |
| 6         | **ResNet50**         | 95.81% ± 3.42%             | 0.9587 ± 0.0337         | 0.9666        | 0.9557       | 24,113,284       | 91.63 MB           | 103.29 ms        |


Tabel 1 menunjukkan bahwa **MobileNetV3Large**, **EfficientNetV2S**, dan **EfficientNetB0** meraih akurasi teratas yang sangat berimbang ($97.19\%\text{--}97.22\%$). Namun, terjadi disparitas efisiensi yang ekstrem: MobileNetV3Large mampu menyamai akurasi model raksasa EfficientNetV2S dengan kecepatan inferensi **7.34× lebih cepat** ($11.40\text{ ms}$ vs $83.70\text{ ms}$) dan ukuran berkas **6.35× lebih ringkas** ($12.30\text{ MB}$ vs $78.12\text{ MB}$). Arsitektur berkapasitas terbesar, ConvNeXtTiny (28.02M params) dan ResNet50 (24.11M params), tidak memberikan peningkatan akurasi yang lebih unggul.

### 3.2 Dinamika Transfer Learning 2-Fase

Perbandingan antara Fase 1 (*Frozen*) dan Fase 2 (*Fine-Tuning*) memperlihatkan wawasan krusial mengenai dinamika pembelajaran pada rezim sampel kecil ($N=143$):

- **Peningkatan Signifikan:** MobileNetV2 meningkat dari $93.74\% \to 95.81\%$ ($+2.07\%$) dan ConvNeXtTiny melonjak dari $95.05\% \to 97.19\%$ ($+2.14\%$). Adaptasi layer konvolusi besar $7 \times 7$ pada ConvNeXtTiny berhasil menyesuaikan filter global ImageNet terhadap tekstur bulu ternak.
- **Saturasi Bobot Optimal:** MobileNetV3Large ($97.22\% \to 97.22\%$) dan EfficientNetB0 ($97.19\% \to 97.19\%$) telah mencapai batas konvergensi optimal sejak Fase 1 berkat kekayaan filter spasial pra-latih ImageNet.
- **Penurunan Minor (*Catastrophic Drift*):** EfficientNetV2S dan ResNet50 mengalami sedikit penurunan akurasi ($-0.69\%$). Kapasitas parameter yang terlampau besar ($>20\text{M}$) pada data latih terbatas ($\sim 115$ sampel per fold) rentan memicu pergeseran bobot representasional (*over-parameterization penalty*).

### 3.3 Evaluasi Metrik Per-Kelas Ras Sapi

Evaluasi terinci pada Tabel 2 membuktikan ketiadaan bias kelas pada model terbaik.

#### Tabel 2. Metrik Per-Kelas Ras Sapi pada Fase 2 (Mean dari 5 Fold CV)


| Model                | Kelas Ras Sapi | Presisi | Recall     | F1-Score   |
| -------------------- | -------------- | :-------: | :----------: | :----------: |
| **MobileNetV3Large** | Sapi Bali      | 1.0000  | 0.9381     | 0.9664     |
|                      | Sapi Brahman   | 0.9750  | 0.9333     | 0.9467     |
|                      | Sapi Brangus   | 0.9778  | **1.0000** | **0.9882** |
|                      | Sapi Limusin   | 0.9600  | **1.0000** | **0.9778** |
| **EfficientNetB0**   | Sapi Bali      | 1.0000  | 0.9381     | 0.9664     |
|                      | Sapi Brahman   | 1.0000  | 0.9381     | 0.9664     |
|                      | Sapi Brangus   | 0.9750  | 1.0000     | 0.9867     |
|                      | Sapi Limusin   | 0.9378  | 1.0000     | 0.9660     |
| **ResNet50**         | Sapi Bali      | 0.9714  | 0.9095     | 0.9379     |
|                      | Sapi Brahman   | 1.0000  | 0.9381     | 0.9664     |
|                      | Sapi Brangus   | 1.0000  | 1.0000     | 1.0000     |
|                      | Sapi Limusin   | 0.8950  | 0.9750     | 0.9306     |


Pada matriks konfusi agregat (143 citra), seluruh model meraih **Recall 100% pada Sapi Brangus (37/37 sampel benar)** berkat warna hitam pekat dan postur tanpa tanduk yang kontras. MobileNetV3Large juga mengidentifikasi seluruh **39 sampel Sapi Limusin secara sempurna (Recall 100%)**. Misklasifikasi minor terkonsentrasi antara Sapi Bali betina dengan Sapi Limusin muda akibat kesamaan gradasi warna bulu merah kecokelatan pada sudut pemotretan jarak jauh.

### 3.4 Validasi Statistik McNemar: Pembuktian Prinsip Occam’s Razor

Uji McNemar berpasangan ($\alpha = 0.05$) menghasilkan nilai $p \ge 0.5000$ **di seluruh pasangan pengujian model** (Tabel 3).

#### Tabel 3. Hasil Uji Signifikansi Statistik McNemar Berpasangan


| Pasangan Model                      | $b$ (A Benar, B Salah) | $c$ (A Salah, B Benar) | Nilai $p$ (*p-value*) | Keterangan Signifikansi ($\alpha = 0.05$) |
| ----------------------------------- | :----------------------: | :----------------------: | :---------------------: | ----------------------------------------- |
| MobileNetV3Large vs MobileNetV2     | 2                      | 0                      | 0.5000                | Tidak Signifikan ($p \ge 0.05$)           |
| MobileNetV3Large vs EfficientNetB0  | 1                      | 1                      | 1.0000                | Tidak Signifikan ($p \ge 0.05$)           |
| MobileNetV3Large vs EfficientNetV2S | 1                      | 1                      | 1.0000                | Tidak Signifikan ($p \ge 0.05$)           |
| MobileNetV3Large vs ConvNeXtTiny    | 1                      | 1                      | 1.0000                | Tidak Signifikan ($p \ge 0.05$)           |
| MobileNetV3Large vs ResNet50        | 4                      | 2                      | 0.6875                | Tidak Signifikan ($p \ge 0.05$)           |
| ConvNeXtTiny vs ResNet50            | 3                      | 1                      | 0.6250                | Tidak Signifikan ($p \ge 0.05$)           |


Hasil ini membuktikan bahwa penambahan parameter hingga sembilan kali lipat tidak memberikan keunggulan performa yang signifikan secara statistik. Sesuai prinsip keilmuan **Occam’s Razor**, arsitektur dengan kompleksitas terendah dan efisiensi tertinggi (**MobileNetV3Large**) adalah pilihan yang paling terjustifikasi secara ilmiah untuk diimplementasikan.

### 3.5 Verifikasi Morfologis Visual Berbasis Grad-CAM

Visualisasi Grad-CAM pada layer konvolusi terakhir (`activation_19`) MobileNetV3Large membuktikan bahwa model mengunci representasi fitur pada karakteristik fenotipik biologis ternak:

- **Sapi Bali (100% keyakinan):** Peta panas terkonsentrasi pada cermin hidung berbingkai putih (*white muzzle*), mata, dan tanduk.
- **Sapi Brahman (100% keyakinan):** Peta panas mengunci punuk bahu (*hump*) dan lipatan gelambir (*dewlap*).
- **Sapi Brangus (100% keyakinan):** Aktivasi merata pada siluet tubuh berotot dan mantel hitam pekat.
- **Sapi Limusin (99% keyakinan):** Peta panas terfokus pada ketebalan otot punggung dan pinggul.

Aktivasi berada sepenuhnya di dalam batas tubuh ternak dan bebas dari bias latar belakang rumput, tanah, atau dinding kandang, mengeliminasi kekhawatiran fenomena *Clever Hans effect*.

### 3.6 Kelayakan Deployment Komputasi Tepi untuk SapiKenal (TKT 5)

Evaluasi komputasi tepi membuktikan keunggulan implementasi MobileNetV3Large:

1. **Responsivitas Real-Time:** Latensi inferensi CPU sebesar **11.40 ms** ($\approx 87\text{ FPS}$) menjamin proses pemindaian kamera pada aplikasi Android berlangsung instan tanpa *lag*.
2. **Kemandirian Offline-First:** Ukuran file **12.30 MB** memungkinkan model disematkan langsung di dalam berkas instalasi APK (`assets/lokal_fp32.tflite`), memungkinkan peternak di daerah pelosok Boyolali melakukan identifikasi luring tanpa internet.
3. **Efisiensi Daya:** Konsumsi daya komputasi ponsel ditekan lebih dari 90% dibanding ConvNeXtTiny (latensi 206.05 ms).

---

# BAB IV: HASIL DAN PEMBAHASAN

## Evaluasi Komparatif Arsitektur Deep Learning dan Kelayakan Deployment SapiKenal

---

## 4.1 Ringkasan Eksperimen dan Protokol Evaluasi

Pengujian komparasi terhadap enam arsitektur convolutional neural network (CNN) dilakukan menggunakan skema **Stratified 5-Fold Cross-Validation** pada dataset 143 citra sapi yang terbagi ke dalam empat ras: Bali ($N=34$), Brahman ($N=33$), Brangus ($N=37$), dan Limusin ($N=39$). Setiap arsitektur melalui dua fase pelatihan (*Feature Extraction* kemudian *Fine-Tuning* pada 30% layer teratas), lalu diuji secara menyeluruh untuk mengukur akurasi klasifikasi, ketahanan statistik, interpretabilitas morfologis visual, serta kelayakan inferensi komputasi tepi (*edge deployment*).

---

## 4.2 Analisis Performa Komparatif 6 Arsitektur CNN

Tabel 4.1 menyajikan rangkuman komparasi performa keenam arsitektur setelah melewati Fase 2 (*Fine-Tuning*), diurutkan berdasarkan kombinasi akurasi, efisiensi ukuran berkas, dan kecepatan inferensi.

### Tabel 4.1 Rangkuman Master Komparasi Performa Klasifikasi dan Efisiensi Deployment


| Peringkat | Arsitektur Model     | Akurasi (%) (*Mean ± Std*) | Macro F1 (*Mean ± Std*) | Presisi Makro | Recall Makro | Jumlah Parameter       | Ukuran TFLite (MB) | Latensi CPU (ms) |
| :---------: | -------------------- | :--------------------------: | :-----------------------: | :-------------: | :------------: | :----------------------: | :------------------: | :----------------: |
| 1         | **MobileNetV3Large** | **97.22% ± 4.03%**         | 0.9698 ± 0.0435         | 0.9782        | 0.9679       | **3,243,396** (3.24 M) | **12.30 MB**       | **11.40 ms**     |
| 2         | **EfficientNetV2S**  | **97.22% ± 2.59%**         | 0.9692 ± 0.0301         | 0.9757        | 0.9688       | 20,660,324 (20.66 M)   | 78.12 MB           | 83.70 ms         |
| 3         | **EfficientNetB0**   | 97.19% ± 3.44%             | **0.9714 ± 0.0351**     | **0.9782**    | **0.9690**   | 4,378,535 (4.38 M)     | 16.56 MB           | 19.31 ms         |
| 4         | **ConvNeXtTiny**     | 97.19% ± 3.44%             | **0.9714 ± 0.0350**     | 0.9773        | **0.9690**   | 28,018,020 (28.02 M)   | 106.96 MB          | 206.05 ms        |
| 5         | **MobileNetV2**      | 95.81% ± 4.06%             | 0.9570 ± 0.0425         | 0.9674        | 0.9545       | **2,586,948** (2.59 M) | **9.72 MB**        | 12.84 ms         |
| 6         | **ResNet50**         | 95.81% ± 3.42%             | 0.9587 ± 0.0337         | 0.9666        | 0.9557       | 24,113,284 (24.11 M)   | 91.63 MB           | 103.29 ms        |


*Catatan: Nilai metrik diperoleh dari rerata 5 lipatan data uji Stratified 5-Fold CV. Latensi diukur pada CPU multi-core (rerata 100 iterasi setelah 10 iterasi pemanasan).*

Berdasarkan Tabel 4.1, temuan empiris utama yang terungkap meliputi:

1. **Puncak Akurasi Berimbang:** Tiga arsitektur teratas (**MobileNetV3Large**, **EfficientNetV2S**, dan **EfficientNetB0**) mencapai tingkat akurasi yang berada pada kisaran sempit $97.19\%\text{--}97.22\%$.
2. **Kestabilan Fold Terunggul:** **EfficientNetV2S** mencatatkan deviasi standar terendah ($\pm 2.59\%$), menandakan sensitivitas yang paling minim terhadap variasi partisi data latih-uji.
3. **Disparitas Efisiensi Ekstrem:** Meskipun memiliki akurasi yang identik dengan EfficientNetV2S ($97.22\%$), **MobileNetV3Large** memiliki latensi **7.34× lebih cepat** ($11.40\text{ ms}$ vs $83.70\text{ ms}$) dan ukuran berkas **6.35× lebih ringkas** ($12.30\text{ MB}$ vs $78.12\text{ MB}$).
4. **Anomali Arsitektur Raksasa:** Arsitektur modern berkapasitas besar seperti **ConvNeXtTiny** (28.02M parameter) dan arsitektur residual klasik **ResNet50** (24.11M parameter) tidak memberikan keunggulan akurasi yang lebih baik dibanding model berukuran 3M-4M parameter, bahkan ResNet50 tertinggal di angka $95.81\%$.

---

## 4.3 Analisis Efek Protokol Pelatihan 2-Fase (Transfer Learning)

Eksperimen membedah dinamika performa antara **Fase 1 (*Feature Extraction* dengan backbone beku)** dan **Fase 2 (*Fine-Tuning* pada 30% layer teratas)**.

### Tabel 4.2 Komparasi Akurasi Antara Fase 1 dan Fase 2 (*Performance Gain / Drift*)


| Arsitektur Model     | Akurasi Fase 1 (Frozen) | Akurasi Fase 2 (Fine-Tuned) | Selisih Akurasi ($\Delta$) | Fenomena Dinamika Pembelajaran                                                         |
| -------------------- | :-----------------------: | :---------------------------: | :--------------------------: | -------------------------------------------------------------------------------------- |
| **MobileNetV3Large** | 97.22%                  | 97.22%                      | $+0.00\%$                  | Representasi fitur ImageNet sudah optimal; konvergensi stabil.                         |
| **MobileNetV2**      | 93.74%                  | 95.81%                      | $+2.07\%$                  | *Domain adaptation* berhasil; layer konvolusi teratas menyerap ciri fenotipe sapi.     |
| **EfficientNetB0**   | 97.19%                  | 97.19%                      | $+0.00\%$                  | Skalasi *compound* mempertahankan generalisasi tanpa pergeseran bobot.                 |
| **EfficientNetV2S**  | 97.91%                  | 97.22%                      | $-0.69\%$                  | Terjadi sedikit *mild overfitting* / *representational drift* pada data kecil.         |
| **ConvNeXtTiny**     | 95.05%                  | 97.19%                      | $+2.14\%$                  | Blok konvolusi $7 \times 7$ memerlukan adaptasi lokal untuk fitur tekstur bulu ternak. |
| **ResNet50**         | 96.50%                  | 95.81%                      | $-0.69\%$                  | Kapasitas layer residual terlalu besar untuk 143 citra, memicu fluktuasi validasi.     |


```
Akurasi (%)
100 ┌────────────────────────────────────────────────────────────────────────┐
 98 │  [97.2] [97.2]                  [97.2] [97.2]  [97.9] [97.2]           │
 96 │                 [93.7] [95.8]                                 [95.1][97.2] [96.5][95.8]
 94 │                                                                        │
 92 └────────────────────────────────────────────────────────────────────────┘
       MobileNetV3L     MobileNetV2    EfficientNetB0  EfficientNetV2S  ConvNeXtTiny    ResNet50
       [■ Fase 1 (Frozen)]  [■ Fase 2 (Fine-Tuned)]
```

### Pembahasan Ilmiah Dinamika Transfer Learning

Fenomena di atas memperlihatkan wawasan krusial mengenai perilaku transfer learning pada **rezim sampel kecil (*small-sample regime*,** $N=143$**)**:

1. **Saturasi Fitur pada Model Efisien:** Pada MobileNetV3Large dan EfficientNetB0, filter spasial yang dipelajari dari ImageNet (seperti tepi, tekstur kurva, dan gradien warna) sudah memiliki daya diskriminasi yang sangat tinggi terhadap postur sapi. Akibatnya, pembaruan gradien pada Fase 2 tidak mengubah batas keputusan (*decision boundary*) secara signifikan.
2. **Kebutuhan Adaptasi pada ConvNeXtTiny:** ConvNeXtTiny mengadopsi patch konvolusi besar ($7 \times 7$) serupa Vision Transformer. Pada Fase 1, filter global ImageNet belum peka terhadap kontur spesifik kepala dan punuk sapi lokal, sehingga proses *fine-tuning* pada Fase 2 memberikan lonjakan performa tertinggi ($+2.14\%$).
3. **Risiko Over-parameterization:** Penurunan akurasi minor ($-0.69\%$) pada ResNet50 dan EfficientNetV2S membuktikan hukum *diminishing returns*: membuka layer konvolusi pada jaringan berbobot $>20\text{M}$ parameter dengan data latih $\sim 115$ citra per fold berisiko merusak bobot representasi umum (*catastrophic drift*) akibat gradien yang terlampau spesifik pada sampel terbatas.

---

## 4.4 Evaluasi Metrik Per-Kelas Ras Sapi dan Matriks Konfusi Agregat

Evaluasi terinci dilakukan untuk memastikan tidak ada kelas ras sapi tertentu yang terabaikan (*class bias*).

### Tabel 4.3 Evaluasi Metrik Presisi, Recall, dan F1-Score per Ras Sapi (Fase 2)


| Arsitektur Model     | Metrik       | Sapi Bali  | Sapi Brahman | Sapi Brangus | Sapi Limusin | Rata-rata Kelas |
| -------------------- | ------------ | :----------: | :------------: | :------------: | :------------: | :---------------: |
| **MobileNetV3Large** | **Presisi**  | **1.0000** | 0.9750       | 0.9778       | 0.9600       | 0.9782          |
|                      | **Recall**   | 0.9381     | 0.9333       | **1.0000**   | **1.0000**   | 0.9679          |
|                      | **F1-Score** | 0.9664     | 0.9467       | **0.9882**   | **0.9778**   | **0.9698**      |
| **MobileNetV2**      | **Presisi**  | **1.0000** | 0.9464       | **1.0000**   | 0.9232       | 0.9674          |
|                      | **Recall**   | 0.9381     | 0.9048       | **1.0000**   | 0.9750       | 0.9545          |
|                      | **F1-Score** | 0.9664     | 0.9181       | **1.0000**   | 0.9433       | 0.9570          |
| **EfficientNetB0**   | **Presisi**  | **1.0000** | **1.0000**   | 0.9750       | 0.9378       | **0.9782**      |
|                      | **Recall**   | 0.9381     | 0.9381       | **1.0000**   | **1.0000**   | **0.9690**      |
|                      | **F1-Score** | 0.9664     | 0.9664       | 0.9867       | 0.9660       | **0.9714**      |
| **EfficientNetV2S**  | **Presisi**  | 0.9500     | **1.0000**   | 0.9528       | **1.0000**   | 0.9757          |
|                      | **Recall**   | **0.9667** | 0.9333       | **1.0000**   | 0.9750       | 0.9688          |
|                      | **F1-Score** | 0.9552     | 0.9600       | 0.9749       | **0.9867**   | 0.9692          |
| **ConvNeXtTiny**     | **Presisi**  | **1.0000** | 0.9714       | **1.0000**   | 0.9378       | 0.9773          |
|                      | **Recall**   | 0.9381     | 0.9381       | **1.0000**   | **1.0000**   | **0.9690**      |
|                      | **F1-Score** | 0.9664     | 0.9532       | **1.0000**   | 0.9660       | **0.9714**      |
| **ResNet50**         | **Presisi**  | 0.9714     | **1.0000**   | **1.0000**   | 0.8950       | 0.9666          |
|                      | **Recall**   | 0.9095     | 0.9381       | **1.0000**   | 0.9750       | 0.9557          |
|                      | **F1-Score** | 0.9379     | 0.9664       | **1.0000**   | 0.9306       | 0.9587          |


### Analisis Matriks Konfusi Agregat (143 Sampel)

Berdasarkan akumulasi prediksi 5-fold cross-validation terhadap seluruh 143 citra:

1. **Sempurnanya Klasifikasi Sapi Brangus (**$N=37$**):**  
Seluruh model (termasuk MobileNetV3Large, EfficientNetB0, ConvNeXtTiny, dan ResNet50) mencatatkan **Recall 100% (37/37 benar)** pada Sapi Brangus. Ciri fenotipik berupa warna bulu hitam pekat seragam dan ketiadaan tanduk memberikan kontras visual yang sangat tegas dibanding ras lainnya.
2. **Keunggulan MobileNetV3Large pada Sapi Limusin (**$N=39$**):**  
MobileNetV3Large berhasil mengidentifikasi seluruh **39 citra Sapi Limusin tanpa satupun kesalahan (*Recall 100%*)**, hanya mengalami 1 misklasifikasi pada Sapi Bali (diprediksi Brahman) dan 1 misklasifikasi pada Sapi Bali (diprediksi Limusin).
3. **Pola Misklasifikasi Minor:**  
Kesalahan klasifikasi terkonsentrasi pada diferensiasi antara **Sapi Bali** dan **Sapi Limusin** (misal pada ResNet50: 3 citra Bali diprediksi Limusin). Hal ini disebabkan kemiripan gradasi warna bulu merah kecokelatan antara Sapi Bali betina dengan Sapi Limusin muda pada sudut pengambilan gambar jarak jauh.

---

## 4.5 Pembuktian Uji Signifikansi Statistik (McNemar's Test)

Untuk menguji apakah perbedaan akurasi antar-model signifikan secara statistik, dilakukan *Pairwise McNemar's Test* dengan koreksi kontinuitas Edwards pada tingkat signifikansi $\alpha = 0.05$.

### Tabel 4.4 Hasil Uji Signifikansi Statistik McNemar Antar-Pasangan Model


| Pasangan Model (Model A vs Model B)     | $b$ (A Benar, B Salah) | $c$ (A Salah, B Benar) | Nilai $p$ (*p-value*) | Signifikan secara Statistik? ($\alpha = 0.05$) |
| --------------------------------------- | :----------------------: | :----------------------: | :---------------------: | :----------------------------------------------: |
| **MobileNetV3Large vs MobileNetV2**     | 2                      | 0                      | 0.5000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV3Large vs EfficientNetB0**  | 1                      | 1                      | 1.0000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV3Large vs EfficientNetV2S** | 1                      | 1                      | 1.0000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV3Large vs ConvNeXtTiny**    | 1                      | 1                      | 1.0000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV3Large vs ResNet50**        | 4                      | 2                      | 0.6875                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV2 vs EfficientNetB0**       | 0                      | 2                      | 0.5000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV2 vs EfficientNetV2S**      | 0                      | 2                      | 0.5000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV2 vs ConvNeXtTiny**         | 0                      | 2                      | 0.5000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **MobileNetV2 vs ResNet50**             | 3                      | 3                      | 1.0000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **EfficientNetB0 vs EfficientNetV2S**   | 2                      | 2                      | 1.0000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **EfficientNetB0 vs ConvNeXtTiny**      | 1                      | 1                      | 1.0000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **EfficientNetB0 vs ResNet50**          | 4                      | 2                      | 0.6875                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **EfficientNetV2S vs ConvNeXtTiny**     | 2                      | 2                      | 1.0000                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **EfficientNetV2S vs ResNet50**         | 5                      | 3                      | 0.7266                | **Tidak Signifikan (**$p \ge 0.05$**)**        |
| **ConvNeXtTiny vs ResNet50**            | 3                      | 1                      | 0.6250                | **Tidak Signifikan (**$p \ge 0.05$**)**        |


### Makna Ilmiah: Landasan Prinsip Occam’s Razor

Seluruh perbandingan pasangan model menghasilkan nilai $p > 0.05$ (rentang $p = 0.5000$ hingga $1.0000$).  
Secara metodologis, ini membuktikan bahwa:

> **Hipotesis nol (**$H_0$**) tidak dapat ditolak.** Tidak ada bukti statistik yang menyatakan bahwa model berkapasitas masif seperti ConvNeXtTiny (28M parameter) atau ResNet50 (24M parameter) mengungguli MobileNetV3Large (3.2M parameter).

Berdasarkan prinsip keilmuan **Occam’s Razor** dan kaidah rekayasa perangkat lunak: ketika dua model komputasi menunjukkan akurasi yang setara secara statistik, maka **model dengan kompleksitas paling rendah dan efisiensi sumber daya tertinggi harus dipilih sebagai model produksi**.

---

## 4.6 Analisis Explainability Visual Menggunakan Grad-CAM

Untuk memverifikasi keabsahan biologis dari fitur yang dipelajari model terbaik (**MobileNetV3Large**), dilakukan ekstraksi peta aktivasi Grad-CAM pada layer konvolusi terakhir (`activation_19`).

```
[Citra Asli]                     [Overlay Grad-CAM Heatmap]           [Fokus Morfologis Biologis]
─────────────────────────────────────────────────────────────────────────────────────────────────
Sapi Bali (100% keyakinan)   ──> Atensi kuat pada cermin hidung   ──> White muzzle, kontur mata,
                                 dan area tanduk melengkung           dan pangkal tanduk khas.
Sapi Brahman (100% keyakinan)──> Puncak panas (merah) terkunci    ──> Punuk besar (hump) & gelambir
                                 pada punuk bahu dan leher            leher longgar (dewlap).
Sapi Brangus (100% keyakinan)──> Atensi merata pada siluet tubuh   ──> Tubuh berotot, ketiadaan tanduk,
                                 dan tekstur mantel hitam             dan pigmentasi hitam legam.
Sapi Limusin (99% keyakinan) ──> Konsentrasi panas pada pinggul    ──> Postur tebal daging dan mantel
                                 dan punggung atas                    merah keemasan (golden-red).
```

### Eliminasi Bias Artefak Latar Belakang (*Clever Hans Effect*)

Hasil visualisasi Grad-CAM mengonfirmasi tiga temuan fundamental:

1. **Fokus Bebas Bias Latar Belakang:** Area dengan aktivasi tertinggi ($>0.8$) sepenuhnya berada di dalam batas kontur tubuh sapi. Area lingkungan sekitar seperti rumput hijau, tanah kandang, atap seng, atau tali pengikat sapi berada pada zona dingin (biru, aktivasi $<0.2$).
2. **Kesesuaian dengan Taksonomi Peternakan:** Model secara mandiri (*unsupervised representation*) menitikberatkan atensi pada bagian tubuh yang memang digunakan oleh peternak dan praktisi lapangan dalam identifikasi manual, seperti **punuk pada Brahman** dan **moncong putih pada Bali**.
3. **Validitas untuk Luaran Jurnal:** Adanya visualisasi XAI ini memberikan tingkat kepercayaan ilmiah (*trustworthiness*) yang tinggi bagi naskah publikasi Sinta 2.

---

## 4.7 Analisis Kelayakan Deployment Edge Device (TFLite &amp; CPU Latency)

Untuk memenuhi target **TKT 5 (Validasi prototipe dalam lingkungan relevan)** pada aplikasi mobile **SapiKenal**, seluruh model dievaluasi berdasarkan parameter komputasi tepi (*edge computing*).

### Tabel 4.5 Analisis Kelayakan Deployment Mobile / Offline-First


| Arsitektur Model     | Ukuran Model TFLite (MB) | Rasio Ukuran vs MobileNetV3L | Latensi Inferensi CPU (ms) | Rasio Kecepatan vs MobileNetV3L | Kelayakan Deployment Android Peternak                |
| -------------------- | :------------------------: | :----------------------------: | :--------------------------: | :-------------------------------: | ---------------------------------------------------- |
| **MobileNetV3Large** | **12.30 MB**             | **1.00× (Baseline)**         | **11.40 ms**               | **1.00× (Tercepat)**            | **Sangat Layak (Optimal)**                           |
| **MobileNetV2**      | **9.72 MB**              | 0.79×                        | 12.84 ms                   | 1.13× lebih lambat              | **Sangat Layak**                                     |
| **EfficientNetB0**   | 16.56 MB                 | 1.35×                        | 19.31 ms                   | 1.69× lebih lambat              | Layak (Beban komputasi sedang)                       |
| **EfficientNetV2S**  | 78.12 MB                 | 6.35×                        | 83.70 ms                   | 7.34× lebih lambat              | Tidak Disarankan (Ukuran membengkak)                 |
| **ResNet50**         | 91.63 MB                 | 7.45×                        | 103.29 ms                  | 9.06× lebih lambat              | Tidak Layak (Lag terasa pada ponsel murah)           |
| **ConvNeXtTiny**     | 106.96 MB                | 8.70×                        | 206.05 ms                  | 18.07× lebih lambat             | Sangat Tidak Layak (&gt;200 ms, konsumsi RAM tinggi) |


```
Trade-off: Akurasi (%) vs Ukuran TFLite (MB) vs Latensi CPU (ms)
──────────────────────────────────────────────────────────────────────
Akurasi (%)
 98 │  ● MobileNetV3L (12.3 MB | 11.4 ms)   ● EfficientNetV2S (78.1 MB | 83.7 ms)
    │  ● EfficientNetB0 (16.6 MB | 19.3 ms) ● ConvNeXtTiny (107.0 MB | 206.1 ms)
 97 │
 96 │  ● MobileNetV2 (9.7 MB | 12.8 ms)     ● ResNet50 (91.6 MB | 103.3 ms)
 95 └──────────────────────────────────────────────────────────────────
    0 MB                   50 MB                  100 MB        Ukuran TFLite
    (Area kiri atas = Pareto Optimal / Sweet Spot: MobileNetV3Large)
```

### Implikasi Praktis bagi Peternak di Lapangan

1. **Responsivitas Real-Time:** Latensi inferensi **11.40 ms** pada MobileNetV3Large setara dengan kecepatan proses $\approx 87\text{ frame per second}$ (FPS). Kecepatan ini menjamin proses pemindaian citra pada kamera Android aplikasi SapiKenal berlangsung instan tanpa jeda visual (*zero lag*).
2. **Kemandirian Offline-First:** Ukuran file **12.30 MB** memungkinkan model disematkan langsung di dalam bundel berkas APK Android (`assets/lokal_fp32.tflite`). Hal ini memungkinkan peternak di wilayah pelosok Boyolali yang minim sinyal internet tetap dapat melakukan klasifikasi jenis sapi secara andal tanpa bergantung pada koneksi internet atau server awan.
3. **Efisiensi Baterai Perangkat:** Dibandingkan ConvNeXtTiny yang membutuhkan waktu $206.05\text{ ms}$ (dan beban kalkulasi $28\text{M}$ operasi matriks), MobileNetV3Large menekan konsumsi daya baterai dan pemanasan CPU ponsel hingga lebih dari **90%**.

---

## 4.8 Kesimpulan Pembahasan

1. **Model Terbaik Terpilih:** **MobileNetV3Large** terbukti secara empiris dan statistik sebagai arsitektur paling optimal, meraih akurasi puncak **97.22% ± 4.03%**, Macro F1 **0.9698**, ukuran TFLite **12.30 MB**, dan latensi inferensi CPU **11.40 ms**.
2. **Justifikasi Ilmiah Kuat:** Uji McNemar membuktikan bahwa arsitektur yang lebih besar tidak memberikan keunggulan akurasi yang signifikan secara statistik ($p > 0.05$).
3. **Verifikasi Morfologis Visual:** Peta panas Grad-CAM membuktikan model membedakan sapi berdasarkan fitur anatomi fenotipik yang valid (punuk Brahman, moncong putih Bali, tubuh berotot Brangus, profil pedaging Limusin).
4. **Kesiapterapan Luaran:** Hasil ini sepenuhnya memvalidasi arsitektur produksi SapiKenal saat ini dan siap digunakan sebagai bukti pencapaian **TKT 5** dalam laporan penelitian hibah PUP Polines serta publikasi Jurnal Nasional Terakreditasi Sinta 2.

---
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

---

### DAFTAR PUSTAKA

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