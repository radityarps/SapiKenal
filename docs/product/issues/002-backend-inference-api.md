# Migrasikan inferensi dan API backend ke jenis sapi

## Tujuan

Menjalankan `best.keras` melalui backend dan mengembalikan hasil empat jenis tanpa kontrak penyakit atau penolakan non-sapi.

## Dependensi

- Issue 001.

## Scope

- Arahkan konfigurasi dan startup fallback ke `model/best.keras`.
- Ganti label dan validasi registry menjadi class order jenis sapi.
- Ganti respons `disease_class` dengan `predicted_class`.
- Hapus `DISPLAY_LABEL_KEY_MAP` penyakit dan jalur `NON_CATTLE_IMAGE`.
- Perlakukan citra yang berhasil diproses sebagai hasil sukses dengan kelas argmax.
- Pertahankan tingkat keyakinan dan empat skor apa adanya, termasuk skor rendah.
- Perbarui OpenAPI, contoh environment, Docker, logging, model registry, dan test backend.
- Jangan memuat model penyakit sebagai fallback tersembunyi.

## Kriteria penerimaan

- [ ] Backend memuat `best.keras` dan status model menjadi ready.
- [ ] Respons sukses hanya memakai `predicted_class`, `confidence`, dan empat skor jenis.
- [ ] Tidak ada respons 422 khusus `non_cattle` dari hasil model.
- [ ] Registry menerima hanya class order final dan menolak urutan lain.
- [ ] Endpoint lama tidak mengklaim deteksi penyakit.
- [ ] Fixture citra dapat mencapai model produksi, bukan hanya mock.
- [ ] Test backend lulus.

## Verifikasi

```bash
pnpm run backend:test
```

Tambahkan smoke test model nyata yang dapat dijalankan di runtime Docker lengkap bila TensorFlow tidak tersedia di virtualenv ringan.
