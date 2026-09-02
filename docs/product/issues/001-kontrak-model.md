# Tetapkan dan validasi kontrak model empat jenis

## Tujuan

Menjadikan urutan kelas, tensor, preprocessing, metadata, dan artefak baru sebagai satu kontrak yang dapat divalidasi otomatis sebelum backend atau mobile menggunakannya.

## Scope

- Tetapkan urutan `bali`, `brahman`, `brangus`, `limusin` dari `class_names.json`.
- Inspeksi `best.keras` dan `jenis_fp32.tflite`: bentuk/tipenya, softmax, ukuran input, serta preprocessing internal.
- Perbarui metadata model dan checksum kedua artefak.
- Tetapkan nama versi model yang sama maknanya untuk backend dan mobile.
- Tambahkan pemeriksaan kecil yang gagal bila metadata, class order, checksum, atau tensor contract menyimpang.
- Putuskan penghapusan final artefak model penyakit yang saat ini sudah dihapus dari working tree; jangan menghapus tanpa mencatatnya pada perubahan ini.

## Di luar scope

- Mengubah UI atau schema riwayat.
- Mengukur akurasi model dari dataset mentah.

## Kriteria penerimaan

- [ ] Metadata menyebut asset/model baru dan tidak menyebut penyakit.
- [ ] Class index 0–3 sama pada Keras, TFLite, backend, dan mobile.
- [ ] Input/output kedua model terverifikasi sebagai kontrak yang didukung runtime.
- [ ] Rentang input, RGB, resize, dan rescaling terdokumentasi berdasarkan isi model atau proses export.
- [ ] Checksum aktual cocok dengan metadata.
- [ ] Model dengan class order atau tensor contract berbeda ditolak.
- [ ] Ada satu perintah runnable untuk memvalidasi kontrak tanpa inferensi UI manual.

## Verifikasi

```bash
python scripts/verify_model_contract.py
```

Jika script tersebut belum ada, implementasi issue ini harus membuat versi minimum tanpa menambah framework baru.
