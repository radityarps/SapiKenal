# Parity Keras–TFLite

## Hasil

Pengukuran 7 September 2026 pada 13 citra nyata yang disediakan tim menghasilkan:

- 13/13 kelas pemenang Keras dan TFLite sama;
- tensor input produksi backend dan Android identik untuk seluruh fixture;
- bentuk input `[1, 224, 224, 3]`, output `[1, 4]`, dan dtype `float32` sama;
- urutan kelas `bali`, `brahman`, `brangus`, `limusin` sama; dan
- selisih skor maksimum `0.000002233688736`.

Citra tidak disimpan di Git. [`parity-baseline.json`](parity-baseline.json)
hanya menyimpan ID dan SHA-256 untuk memastikan regression check memakai
corpus dan artefak yang sama.

## Preprocessing produksi

Android mengoreksi orientasi EXIF, melakukan resize bilinear ke 224 × 224 satu
kali, lalu mengenkode PNG lossless. Byte yang sama digunakan oleh inferensi
TFLite dan dikirim ke backend. Backend mendekode PNG sebagai RGB; resize
224 × 224 menjadi no-op. Kedua model menerima kanal RGB float32 mentah dalam
rentang 0–255 dan menjalankan rescaling internal `(x / 127.5) - 1`.

Pendekatan ini menggantikan pipeline awal yang melakukan JPEG lossless-unsafe
dan resize melalui implementasi berbeda. Baseline awal tersebut menghasilkan
satu winner mismatch serta selisih piksel hingga 49; hasil itu ditolak dan tidak
menjadi toleransi aktif.

## Toleransi terukur

Toleransi skor aktif adalah `0.000003`, yaitu pembulatan ke atas enam desimal
dari maksimum terukur `0.000002233688736`. Toleransi input adalah tepat `0`.
Regression check tetap gagal tanpa memperhatikan toleransi apabila satu kelas
pemenang berbeda, tensor input tidak identik, checksum berubah, runtime berubah,
atau baseline tidak berstatus `accepted`.

Lingkungan baseline: TensorFlow 2.21.0, Pillow 12.3.0, NumPy 2.5.2, TFLite
runtime 2.18.0, perangkat INFINIX X678B Android 14/API 34. Checksum artefak dan
fixture lengkap tercatat dalam baseline JSON.

## Menjalankan ulang

Siapkan satu atau lebih JPEG nyata pada setiap folder `bali/`, `brahman/`,
`brangus/`, dan `limusin/`. Corpus bersifat lokal dan diabaikan Git. Setelah
APK debug serta test APK terpasang pada satu perangkat yang dipilih eksplisit:

```bash
python scripts/capture_android_parity.py \
  --fixtures /path/to/corpus \
  --serial "$ANDROID_SERIAL" \
  --output .parity/current

docker run --rm --network none --user "$(id -u):$(id -g)" \
  -e PYTHONPATH=/workspace/apps/backend \
  -e MODEL_STARTUP_FALLBACK_ENABLED=false \
  -e TF_NUM_INTRAOP_THREADS=1 -e TF_NUM_INTEROP_THREADS=1 \
  -v "$PWD:/workspace:ro" -v "$PWD/.parity/current:/capture" \
  -w /workspace/apps/backend backend-backend \
  python /workspace/scripts/measure_model_parity.py \
    --capture /capture --output /capture/report.json \
    --baseline /workspace/docs/model/parity-baseline.json
```

Capture berisi citra, tensor, dan hasil perangkat sehingga `.parity/` tidak
boleh di-commit.

## Batasan

Corpus ini menguji konsistensi dua runtime, bukan akurasi model, kepastian jenis,
atau validasi bahwa citra memuat sapi. Hasil parity bukan bukti production
readiness. Smoke backend nyata, smoke TFLite nyata, migration/seed rehearsal,
serta rehearsal kamera, galeri, permission denial, online/offline/fallback,
history, PDF, large text, dan TalkBack tetap wajib sebelum rilis.
