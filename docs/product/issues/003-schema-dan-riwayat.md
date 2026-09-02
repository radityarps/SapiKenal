# Reset schema hasil identifikasi dan riwayat

## Tujuan

Mengganti penyimpanan hasil penyakit dengan schema baru yang menyimpan hasil identifikasi jenis dan skor berlabel tanpa membawa semantik lama.

## Dependensi

- Issue 001.

## Scope

- Buat baseline/migrasi schema pengembangan baru sesuai strategi reset yang telah dipilih.
- Ganti kolom skor penyakit dengan `scores` berlabel kanonik.
- Gunakan `predicted_class` untuk kelas teratas.
- Hapus semantik `outcome=rejected`, `rejection_reason=non_cattle`, dan statistik penolakan model.
- Perbarui model ORM, SQLite history store, schema API, sinkronisasi mobile, seed, dan fixture.
- Dokumentasikan perintah reset database nonproduksi dengan guardrail yang jelas.
- Jangan menulis migrasi data penyakit ke jenis sapi karena tidak ada pemetaan domain yang valid.

## Kriteria penerimaan

- [ ] Database baru dapat dibuat dari nol melalui perintah repository.
- [ ] Satu hasil menyimpan kelas teratas dan tepat empat skor jenis.
- [ ] Round-trip API ↔ database ↔ mobile mempertahankan semua skor.
- [ ] Tidak ada kolom `score_fmd`, `score_lsd`, `score_healthy`, atau `score_non_cattle` pada schema baru.
- [ ] Reset tidak berjalan otomatis terhadap database produksi.
- [ ] Test schema, history store, dan sinkronisasi lulus.

## Verifikasi

```bash
pnpm run backend:test
pnpm run mobile:test
```
