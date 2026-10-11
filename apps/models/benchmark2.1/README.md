# Benchmark 2.1 — Perbandingan 8 Arsitektur Deep Learning (Sapi Lokal 7-Kelas)

Direktori ini berisi berkas eksperimen dan notebook perbandingan **8 arsitektur deep learning** (Pure CNN dan Hybrid Edge Vision Transformer) untuk klasifikasi 7 kelas sistem produksi SapiKenal menggunakan dataset [Roboflow Universe `valll-rtclj/sapi-lokal/2`](https://universe.roboflow.com/valll-rtclj/sapi-lokal/dataset/2).

---

## 🎯 Tujuan & Kebaruan Benchmark 2.1

1. **Evaluasi 7 Kelas Riil Sistem Produksi:**  
   Menyelaraskan evaluasi dengan kontrak kelas sistem aktif di [`apps/backend/model/class_names.json`](../../backend/model/class_names.json):
   - **6 Ras Sapi:** `aceh`, `bali`, `limusin`, `madura`, `pasundan`, `po`
   - **1 Kelas Penolakan:** `non_sapi` (*negative rejection class*)
2. **Mitigasi *Severe Class Imbalance*:**  
   Dataset memiliki rentang sampel ekstrem: dari 9 citra (`aceh`) hingga 176 citra (`non_sapi`). Benchmark ini menerapkan:
   - **Balanced Class Weighting** ($w_j = \frac{N}{K \times N_j}$) pada *categorical cross-entropy loss*.
   - **Stratified 5-Fold Cross-Validation** dengan augmentasi *on-the-fly*.
   - Pelaporan metrik berbasis **Macro F1-Score** dan evaluasi per-kelas untuk mencegah bias kelas mayoritas.
3. **Eksplorasi Lintas Paradigma (8 Arsitektur):**  
   Menambahkan **DenseNet121** (unggul dalam *feature reuse* pada data minim) dan **MobileViT-XS** (menguji *global self-attention* Transformer pada komputasi tepi mobile).

---

## 📊 Matriks 8 Arsitektur Model

| No | Arsitektur | Paradigma | Estimasi Params | Fokus Pengujian dalam Benchmark 2.1 |
|:---:|---|---|:---:|---|
| 1 | **MobileNetV3Large** | Mobile / Hardware-Aware NAS | ~3.2M | Baseline produksi SapiKenal (juara Benchmark 2.0). |
| 2 | **MobileNetV2** | Inverted Residuals (Ultra-light) | ~2.6M | Pembanding efisiensi komputasi tepi paling hemat. |
| 3 | **EfficientNetB0** | Compound Scaling v1 | ~4.4M | Penskalaan terimbang kedalaman, lebar, dan resolusi. |
| 4 | **DenseNet121** 🌟 | Dense Feature Concatenation | **~7.0M** | Menguji ketahanan *feature reuse* pada sampel minoritas (`aceh`, `pasundan`). |
| 5 | **EfficientNetV2S** | Progressive Learning & Fused-MBConv | ~20.7M | Menguji kapasitas skala menengah pada 7 kelas. |
| 6 | **ConvNeXtTiny** | Pure CNN berprinsip Swin Transformer | ~28.0M | Arsitektur modern kernel besar $7\times 7$ generasi terbaru. |
| 7 | **ResNet50** | Residual Learning ($x + F(x)$) | ~24.1M | Baseline klasik komparasi di literatur visi komputer. |
| 8 | **MobileViT-XS** 🌟 | Hybrid CNN-Transformer (Global Attention) | **~2.3M** | Menguji apakah *self-attention* lebih bersih memisahkan sapi vs `non_sapi`. |

---

## 🔬 Berkas Notebook

Tersedia opsi eksekusi paralel untuk menghemat waktu komputasi, serta notebook tunggal terpadu:

### Opsi A: Eksekusi Paralel (Disarankan — Estimasi ~80 Menit)
1. [`benchmark2_1_colab.ipynb`](./benchmark2_1_colab.ipynb) — **Part A (Google Colab T4 GPU)**
   - Menjalankan 4 model ringan: `MobileNetV3Large`, `MobileNetV2`, `EfficientNetB0`, `DenseNet121`.
   - Menghasilkan: `all_results_partA.pkl` dan `deployment_partA.pkl`.
2. [`benchmark2_1_kaggle.ipynb`](./benchmark2_1_kaggle.ipynb) — **Part B (Kaggle T4 / P100 GPU)**
   - Menjalankan 4 model berat & ViT: `EfficientNetV2S`, `ConvNeXtTiny`, `ResNet50`, `MobileViT-XS`.
   - Menghasilkan: `all_results_partB.pkl` dan `deployment_partB.pkl`.
3. [`benchmark2_1_merge.ipynb`](./benchmark2_1_merge.ipynb) — **Part C (Merge & Analisis Final)**
   - Menggabungkan hasil Part A & B.
   - Menghasilkan Tabel Master, Tabel Per-Kelas, Heatmap Matriks Konfusi 7-Kelas, Uji McNemar $8\times 8$, dan Grafik *Trade-off* Deployment.

### Opsi B: Eksekusi Tunggal (All-in-One)
* [`benchmark2_1_model_comparison.ipynb`](./benchmark2_1_model_comparison.ipynb) — **Notebook Lengkap**
  - Menjalankan ke-8 model secara sekuensial dalam satu sesi (*direkomendasikan jika menggunakan GPU A100/V100 atau sesi Colab Pro*).

---

## 🚀 Panduan Menjalankan Eksperimen

1. **Jalankan Part A di Google Colab:**
   - Unggah [`benchmark2_1_colab.ipynb`](./benchmark2_1_colab.ipynb).
   - Aktifkan GPU T4: *Runtime > Change runtime type > T4 GPU*.
   - Jalankan semua sel (`Ctrl+F9`). Unduh berkas ZIP hasil `benchmark2_1_outputs_partA.zip`.
2. **Jalankan Part B di Kaggle:**
   - Buat Notebook baru di Kaggle, impor [`benchmark2_1_kaggle.ipynb`](./benchmark2_1_kaggle.ipynb).
   - Aktifkan Accelerator *GPU T4 x2* atau *GPU P100* di panel *Settings*.
   - Aktifkan *Internet ON*.
   - Jalankan semua sel (*Run All*). Unduh berkas ZIP dari tab *Output*.
3. **Jalankan Part C (Merge):**
   - Buka [`benchmark2_1_merge.ipynb`](./benchmark2_1_merge.ipynb) di Colab atau lokal.
   - Unggah berkas `all_results_partA.pkl`, `all_results_partB.pkl`, `deployment_partA.pkl`, `deployment_partB.pkl`.
   - Jalankan semua sel untuk mengekstrak seluruh metrik dan visualisasi publikasi.

---

## 📁 Daftar Artefak Luaran (`benchmark2_1_outputs/`)

| Berkas | Deskripsi |
|---|---|
| `benchmark2_1_master_table.csv` | Rangkuman utama: Macro F1, Akurasi, Presisi, Recall, Ukuran TFLite, Latensi CPU |
| `benchmark2_1_per_class_metrics.csv` | Precision, Recall, F1 untuk masing-masing dari 7 kelas |
| `mcnemar_test_results_8x8.csv` | Matriks perbandingan signifikansi statistik $8\times 8$ ($\alpha = 0.05$) |
| `confusion_matrices_7class.png` | Matriks konfusi agregat 5 fold untuk ke-8 model |
| `tradeoff_chart_8models.png` | Scatter plot Pareto trade-off: Macro F1 vs Latensi CPU vs Ukuran TFLite |
| `all_results_merged.pkl` | Checkpoint mentah seluruh probabilitas dan prediksi per fold |
| `deployment_merged.pkl` | Data profil latensi CPU dan ukuran model TFLite |
