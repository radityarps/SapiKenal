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

- [x] Database baru dapat dibuat dari nol melalui perintah repository.
- [x] Satu hasil menyimpan kelas teratas dan tepat empat skor jenis.
- [x] Round-trip API ↔ database ↔ mobile mempertahankan semua skor.
- [x] Tidak ada kolom `score_fmd`, `score_lsd`, `score_healthy`, atau `score_non_cattle` pada schema baru.
- [x] Reset tidak berjalan otomatis terhadap database produksi.
- [x] Test schema, history store, dan sinkronisasi lulus.

## Workflow reset nonproduksi

Gunakan hanya untuk database SQLite lokal yang boleh dihapus. Perintah ini menghapus
`admin.sqlite3` dan `history.sqlite3`, lalu membuat schema baru dan (jika diatur)
menjalankan seed admin:

```bash
FASTAPI_ENV=development DEBUG=true pnpm run backend:dev
```

`backend:dev` menolak `FASTAPI_ENV` non-development, `DEBUG` selain `true`, dan
`DATABASE_URL` non-SQLite. Script reset Python dijalankan oleh perintah ini dengan
`ALLOW_DEV_DB_RESET=true`; nilainya default `false` untuk pemanggilan langsung,
sehingga database produksi atau database tanpa guard tersebut tidak pernah di-reset
otomatis. Perintah ini menghapus database yang ditunjuk `DATABASE_URL` dan
`HISTORY_DB_PATH`; jangan gunakan pada database yang berisi data yang harus
dipertahankan.

Untuk deployment yang mempertahankan database, jalankan migrasi secara terkontrol:

```bash
pnpm run backend:migrate
```

Migrasi Alembic `0006_four_class_prediction_contract` tidak memetakan data penyakit
ke jenis sapi. Pada SQLite, migrasi hanya mengganti tabel legacy yang kosong; jika
masih ada baris legacy, migrasi berhenti dan meminta backup/reset eksplisit.
PostgreSQL sengaja ditolak sampai tersedia rencana migrasi data eksplisit.

## Verifikasi

```bash
pnpm run backend:test
pnpm run mobile:test
```
