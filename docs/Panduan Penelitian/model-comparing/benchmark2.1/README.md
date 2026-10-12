# Dokumentasi Naskah Komparasi Model Benchmark 2.1 (SapiKenal)

Direktori ini memuat laporan ringkas publikasi ilmiah berstandar jurnal nasional terakreditasi (target Sinta 2 / IEEE) terkait studi komparasi **8 arsitektur deep learning** (Pure CNN dan Hybrid Edge Vision Transformer) pada **7 kelas sistem produksi SapiKenal** (6 ras sapi lokal Indonesia dan 1 kelas penolakan non-sapi).

---

## 1. Berkas Naskah Utama

| Berkas | Status | Deskripsi |
|---|---|---|
| [`LAPORAN_RINGKAS_JURNAL.md`](./LAPORAN_RINGKAS_JURNAL.md) | Selesai (Bahan Publikasi) | Laporan ringkas berstandar jurnal ilmiah (IMRAD), tanpa emoji icon, mencakup Abstrak dwi-bahasa (ID & EN), Tabel Sebaran Kelas, Formulasi Balanced Class Weighting, Tabel Master 8 Model, Analisis Kurva Pareto Trade-off, Metrik Per-Kelas Ras Sapi, Analisis Matriks Konfusi 7-Kelas, Uji Signifikansi Statistik McNemar 8x8, serta 15 Daftar Pustaka format IEEE. |

---

## 2. Aset Gambar dan Data Hasil Benchmark 2.1 (`assets/`)

Seluruh visualisasi dan tabel pada naskah ini bersumber langsung dari hasil eksekusi eksperimen Benchmark 2.1:

| Berkas | Tipe | Deskripsi Konten |
|---|---|---|
| [`assets/tradeoff_chart_8models.png`](./assets/tradeoff_chart_8models.png) | Visualisasi | Scatter plot analisis Pareto trade-off antara Macro F1-Score (sumbu-Y), Latensi CPU Android (sumbu-X), dan Ukuran Berkas TFLite FP32 (diameter gelembung) untuk 8 model. |
| [`assets/confusion_matrices_7class.png`](./assets/confusion_matrices_7class.png) | Visualisasi | Heatmap matriks konfusi agregat (5-Fold Cross-Validation, total 313 citra) untuk seluruh 8 arsitektur model pada 7 kelas. |
| [`assets/benchmark2_1_master_table.csv`](./assets/benchmark2_1_master_table.csv) | Data Tabel | Tabel master metrik klasifikasi (Macro F1, Akurasi, Presisi, Recall) dan metrik deployment komputasi tepi (Parameter, Ukuran TFLite, Latensi CPU). |
| [`assets/benchmark2_1_per_class_metrics.csv`](./assets/benchmark2_1_per_class_metrics.csv) | Data Tabel | Rincian metrik Presisi, Recall, dan F1-Score per kelas (aceh, bali, limusin, madura, non_sapi, pasundan, po) untuk setiap model. |
| [`assets/mcnemar_test_results_8x8.csv`](./assets/mcnemar_test_results_8x8.csv) | Data Tabel | Matriks hasil uji signifikansi statistik Pairwise McNemar 8x8 (28 pasangan pengujian) dengan nilai p dan kesimpulan signifikansi formal (alpha = 0.05). |

---

## 3. Tautan Berkas Notebook Eksperimen

Notebook eksekusi terisolasi yang menghasilkan artefak di atas tersimpan pada:
- Part A (Lightweight CNNs - Colab T4): [`apps/models/benchmark2.1/benchmark2_1_colab.ipynb`](../../../apps/models/benchmark2.1/benchmark2_1_colab.ipynb)
- Part B (Heavy & Hybrid ViT - Kaggle T4/P100): [`apps/models/benchmark2.1/benchmark2_1_kaggle.ipynb`](../../../apps/models/benchmark2.1/benchmark2_1_kaggle.ipynb)
- Part C (Merge & Analisis Final): [`apps/models/benchmark2.1/benchmark2_1_merge.ipynb`](../../../apps/models/benchmark2.1/benchmark2_1_merge.ipynb)
- Unified All-in-One Runner: [`apps/models/benchmark2.1/benchmark2_1_model_comparison.ipynb`](../../../apps/models/benchmark2.1/benchmark2_1_model_comparison.ipynb)
