# Migrasikan inferensi mobile online dan offline

## Tujuan

Menggunakan `lokal_fp32.tflite` untuk mode offline dan kontrak API enam kelas untuk mode online dengan hasil yang konsisten.

## Dependensi

- Issue 001.
- Issue 002.

## Scope

- Ubah `MODEL_FILE_NAME`, versi model, dan konfigurasi contoh ke asset baru.
- Ganti label/display label/skor offline menjadi Aceh, Bali, Limusin, Madura, Pasundan, dan PO.
- Hapus perlakuan kelas keempat sebagai `non_cattle`.
- Sesuaikan DTO online dari `disease_class` ke `predicted_class`.
- Pastikan router/fallback mempertahankan mode, skor, versi model, dan tingkat keyakinan.
- Perbarui unit test dan instrumentation smoke test agar menjalankan TFLite yang benar.
- Pertahankan validasi bentuk tensor, dtype, probabilitas finite, dan jumlah skor.

## Kriteria penerimaan

- [x] APK memuat `lokal_fp32.tflite`, bukan asset penyakit.
- [x] Offline inference mengembalikan tepat enam label final.
- [x] Online inference dapat mem-parsing respons backend baru.
- [x] Tidak ada hasil offline yang ditolak berdasarkan kelas di luar kontrak enam kelas.
- [x] Mode fallback online/offline tetap bekerja sesuai pengaturan saat ini.
- [ ] Smoke test TFLite menjalankan asset produksi pada perangkat/emulator.
- [x] Unit test Android lulus.

## Verifikasi

```bash
pnpm run mobile:test
```

Instrumentation smoke test tersedia di `OfflineInferenceEngineSmokeTest`; jalankan pada emulator/perangkat dengan `cd apps/mobile && bash ./gradlew connectedDebugAndroidTest` sebagai bagian penerimaan issue.
