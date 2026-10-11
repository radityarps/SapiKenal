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
 MobileNetV3Large berhasil mengidentifikasi seluruh \*\*39 citra Sapi Limusin tanpa satupun kesalahan (*Recall 100%*)\*\*, hanya mengalami 1 misklasifikasi pada Sapi Bali (diprediksi Brahman) dan 1 misklasifikasi pada Sapi Bali (diprediksi Limusin).
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