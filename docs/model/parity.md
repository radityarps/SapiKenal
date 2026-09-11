# Parity Keras–TFLite

## Status

Baseline yang tercatat pada 7 September 2026 adalah bukti untuk artefak v1
empat kelas dan sekarang berstatus `blocked`; baseline itu tidak boleh dipakai
sebagai bukti parity untuk kontrak aktif v2. Kontrak aktif memakai input
`[1, 224, 224, 3]`, output `[1, 6]`, dtype `float32`, dan urutan `aceh`,
`bali`, `limusin`, `madura`, `pasundan`, `po`.

Citra tidak disimpan di Git. Buat capture perangkat baru untuk keenam folder
kelas lalu ukur dan tinjau baseline v2 sebelum mengubah statusnya menjadi
`accepted`.

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

Tidak ada toleransi parity aktif untuk v2 sampai capture perangkat baru diukur.
Regression check sengaja gagal ketika baseline berstatus selain `accepted`.
Checksum artefak dan fixture untuk baseline baru harus dicatat dalam baseline
JSON setelah hasilnya ditinjau.

## Menjalankan ulang

Siapkan satu atau lebih JPEG nyata pada setiap folder `aceh/`, `bali/`,
`limusin/`, `madura/`, `pasundan/`, dan `po/`. Corpus bersifat lokal dan diabaikan Git. Setelah
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
