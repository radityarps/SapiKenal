# Dokumentasi Naskah Komparasi Model Deep Learning (SapiKenal)

Direktori ini memuat draf naskah publikasi ilmiah (target **Jurnal Nasional Terakreditasi Sinta 2** dan **Seminar Nasional**) serta laporan penelitian terkait studi komparasi arsitektur deep learning untuk klasifikasi jenis sapi.

---

## 📑 Berkas Naskah Utama

| Berkas | Status | Deskripsi |
|---|---|---|
| 🌟 **[`MANUSKRIP_LENGKAP.md`](./MANUSKRIP_LENGKAP.md)** | ✅ **Selesai (Siap Submit)** | **Naskah Lengkap Terpadu (1 File)**. Mengintegrasikan Judul (Dwi-bahasa), Identitas Tim Peneliti Polines, Abstrak & Kata Kunci (ID & EN), Bab I Pendahuluan, Bab II Metodologi, Bab III Hasil & Pembahasan, Bab IV Kesimpulan, Ucapan Terima Kasih (P3M Polines), dan 23 Daftar Pustaka format IEEE yang disinkronkan secara presisi dengan berkas PDF riil pada direktori `Jurnal Rujukan/`. |
| 📄 **[`LAPORAN_RINGKAS_JURNAL.md`](./LAPORAN_RINGKAS_JURNAL.md)** | ✅ **Selesai (Bahan Jurnal Dosen)** | **Laporan Ringkas Berstandar Jurnal Ilmiah (IMRAD)**. Disusun padat dan lugas tanpa basa-basi (*zero-fluff*) khusus untuk bahan publikasi dosen (Ir. Handoko, M.T. dkk.), tanpa ucapan terima kasih, mencakup Abstrak dwi-bahasa, Tabel Master, Uji McNemar, Grad-CAM, Profiling TFLite CPU, dan 28 Daftar Pustaka format IEEE. |

---

## 📁 Berkas Modular per Bab (Untuk Referensi & Editing Terpisah)

| Berkas | Deskripsi |
|---|---|
| [`PENDAHULUAN.md`](./PENDAHULUAN.md) | Bab I: Pendahuluan, latar belakang Boyolali, batasan metode visual, *research gaps*, dan 4 pilar kebaruan. |
| [`TINJAUAN_PUSTAKA.md`](./TINJAUAN_PUSTAKA.md) | Bab II: Tinjauan Pustaka & Peta Jalan, sistem informasi peternakan, evolusi CNN, sintesis literatur, matriks studi terdahulu, potensi Boyolali, posisi riset, dan Road Map 8 tahap (Gantt Chart 32 minggu). |
| [`METODOLOGI.md`](./METODOLOGI.md) | Bab III: Metodologi, kerangka CRISP-DM, dataset 4 ras, 5-Fold Stratified CV, 6 arsitektur CNN, 2-phase training, uji McNemar, Grad-CAM, dan profil TFLite. |
| [`HASIL_DAN_PEMBAHASAN.md`](./HASIL_DAN_PEMBAHASAN.md) | Bab IV: Hasil dan Pembahasan, tabel master komparasi, analisis transfer learning 2-fase, metrik per-kelas, heatmap matriks konfusi agregat, uji McNemar, Grad-CAM, dan kelayakan deployment. |
| [`KESIMPULAN.md`](./KESIMPULAN.md) | Bab V: Kesimpulan dan Saran, justifikasi Occam's razor, implikasi teoritis & praktis, batasan penelitian, dan rekomendasi riset lanjutan. |

---

## 🎨 Berkas Diagram Vektor (Format Draw.io)

Tersedia berkas diagram arsitektur dan metodologi dalam format asli vector `.drawio` di direktori [`assets/`](./assets/) yang siap dibuka langsung di [app.diagrams.net](https://app.diagrams.net) maupun ekstensi VS Code Draw.io:

| Berkas Diagram | Asal Bab | Deskripsi Diagram |
|---|---|---|
| 📐 [**`kebaruan_penelitian.drawio`**](./assets/kebaruan_penelitian.drawio) | [`PENDAHULUAN.md`](./PENDAHULUAN.md) | 4 Pilar Kebaruan & Kontribusi Ilmiah Riset SapiKenal (Multi-Arsitektur, 5-Fold CV, McNemar, XAI & Edge). |
| 📐 [**`road_map_penelitian.drawio`**](./assets/road_map_penelitian.drawio) | [`TINJAUAN_PUSTAKA.md`](./TINJAUAN_PUSTAKA.md) | Peta Jalan Riset SapiKenal 8 Tahap (Fase 1 Riset & Benchmarking Model -> Fase 2 Rekayasa Sistem & Hilirisasi TKT 5). |
| 📐 [**`metodologi_crisp_dm.drawio`**](./assets/metodologi_crisp_dm.drawio) | [`METODOLOGI.md`](./METODOLOGI.md) | Alur Lengkap Metodologi CRISP-DM 5-Fase: Data Understanding, Prep & Augmentasi, Modeling 2-Fase, Evaluasi & XAI, Deployment Profiling. |
| 📐 [**`taksonomi_arsitektur_cnn.drawio`**](./assets/taksonomi_arsitektur_cnn.drawio) | [`METODOLOGI.md`](./METODOLOGI.md) | Taksonomi 6 Arsitektur CNN: Arsitektur Ringan (Mobile), Skala Kompon (Compound), dan Arsitektur Dalam (High Capacity). |

---

## 🔬 Tautan Artefak Eksperimen (Benchmark 2.0)

Seluruh angka, tabel, dan grafik pada naskah ini bersumber langsung dari artefak validasi **Benchmark 2.0**:
- Master Table: [`apps/models/benchmark2.0/benchmark2_master_table.csv`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/benchmark2_master_table.csv)
- Per-Class Metrics: [`apps/models/benchmark2.0/benchmark2_per_class_metrics.csv`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/benchmark2_per_class_metrics.csv)
- McNemar's Test: [`apps/models/benchmark2.0/mcnemar_test_results.csv`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/mcnemar_test_results.csv)
- Visualisasi:
  - Confusion Matrices: [`apps/models/benchmark2.0/confusion_matrices_phase2.png`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/confusion_matrices_phase2.png)
  - Grad-CAM Explainability: [`apps/models/benchmark2.0/gradcam_examples.png`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/gradcam_examples.png)
  - Fold Variability: [`apps/models/benchmark2.0/fold_variability.png`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/fold_variability.png)
  - Phase Comparison: [`apps/models/benchmark2.0/phase_comparison.png`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/phase_comparison.png)
  - Deployment Tradeoff: [`apps/models/benchmark2.0/tradeoff_chart.png`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2.0/tradeoff_chart.png)
