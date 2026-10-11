# Model Benchmarking & Eksperimen Komparasi

Direktori ini berisi berkas eksperimen dan perbandingan arsitektur deep learning untuk klasifikasi jenis sapi. Eksperimen di direktori ini dirancang terisolasi agar tidak mengganggu model produksi aktif di `apps/backend/model/best.keras` dan `apps/mobile/app/src/main/assets/lokal_fp32.tflite`.

---

## 🔬 Berkas Notebook

### [`benchmark2_model_comparison.ipynb`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark2_model_comparison.ipynb) ⭐ _Terbaru_

Notebook utama untuk penelitian. Melakukan perbandingan **6 arsitektur CNN** dengan metodologi yang ketat:

| Arsitektur | Keterangan |
|---|---|
| **MobileNetV3Large** | Baseline SapiKenal (production) |
| **MobileNetV2** | Paling ringan, referensi deployment |
| **EfficientNetB0** | Compound scaling |
| **EfficientNetV2S** | Generasi terbaru EfficientNet |
| **ConvNeXtTiny** | CNN modern setara Vision Transformer |
| **ResNet50** | Baseline klasik di literatur |

**Metodologi:**
- **5-Fold Stratified Cross-Validation** — evaluasi reliable, semua 143 gambar terpakai
- **2-Phase Training** — Feature Extraction (frozen backbone) → Fine-Tuning (unfreeze top 30%)
- **Evaluasi komprehensif** — Per-class P/R/F1, Grad-CAM, McNemar's test
- **Evaluasi deployment** — TFLite size & latency CPU

### [`benchmark_model_comparison.ipynb`](file:///home/raditya/Projects/SapiKenal/apps/models/benchmark_model_comparison.ipynb) _(Versi 1.0 — Referensi)_

Versi awal dengan 4 arsitektur, single split, feature extraction only. Disimpan sebagai referensi historis.

---

## 🚀 Panduan Menjalankan di Google Colab (Free Tier)

### Benchmark 2.0 (Direkomendasikan)

1. **Buka Google Colab** → Upload `benchmark2_model_comparison.ipynb`
2. **Aktifkan GPU T4**: Runtime → Change runtime type → T4 GPU → Save
3. **Isi API Key Roboflow** di Cell 4: ganti `"YOUR_ROBOFLOW_API_KEY_HERE"` atau `"oSqbdWgbnJkiVfOWl18o"` dengan API key Anda
4. **Jalankan semua**: Runtime → Run all (`Ctrl+F9`)
5. **Estimasi waktu**: ~2–3 jam di T4 (60 training runs)

> **Tip:** Jika terdisconnect, set `RESUME = True` di Cell 8 dan jalankan ulang — checkpoint tersimpan otomatis per model.

### Output yang Dihasilkan (`/content/benchmark2_outputs/`)

| File | Isi |
|---|---|
| `benchmark2_master_table.csv` | Tabel utama: accuracy, F1, params, TFLite, latency |
| `benchmark2_results_summary.csv` | Phase 1 vs Phase 2 per model |
| `benchmark2_per_class_metrics.csv` | Precision/Recall/F1 per kelas per model |
| `benchmark2_fold_details.csv` | Detail tiap fold |
| `confusion_matrices_phase2.png` | Confusion matrix agregat 6 model |
| `fold_variability.png` | Box plot variabilitas antar fold |
| `phase_comparison.png` | Perbandingan Phase 1 vs Phase 2 |
| `tradeoff_chart.png` | Accuracy vs TFLite Size vs Latency |
| `gradcam_examples.png` | Visualisasi Grad-CAM model terbaik |
| `mcnemar_test_results.csv` | Uji signifikansi statistik pairwise |

Simpan folder output ke direktori `benchmark2.0/` di repository ini.

---

## 📁 Hasil Benchmark

| Direktori | Keterangan |
|---|---|
| [`benchmark1.0/`](./benchmark1.0/) | Hasil Benchmark v1.0 (4 model, single split) — referensi |
| [`benchmark2.0/`](./benchmark2.0/) | Hasil Benchmark v2.0 (6 model, 5-Fold Stratified CV, 2-Phase Training, TFLite Deployment, McNemar Test, Grad-CAM) — **Selesai** |

