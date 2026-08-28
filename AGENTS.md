# Agent Instructions — SapiKenal

## Purpose

SapiKenal mengidentifikasi jenis sapi dari citra. Repository ini memakai aplikasi lama sebagai fondasi, tetapi fitur, dokumentasi, dan istilah baru harus mengarah ke identifikasi jenis sapi, bukan deteksi penyakit.

## Read First

Sebelum mengubah dokumentasi atau kode:

1. Baca `CONTEXT.md` untuk istilah domain.
2. Baca `README.md` untuk struktur dan perintah root.
3. Periksa implementasi aktual di `apps/mobile`, `apps/backend`, dan `apps/web` sebelum membuat klaim teknis.

## Documentation

Dokumentasi proyek disimpan di:

- `docs/architecture/`
- `docs/dataset/`
- `docs/model/`
- `docs/api/`
- `docs/mobile/`

Jangan menambahkan kembali proposal, laporan Tugas Akhir, pedoman kampus, evidence audit, atau referensi akademik dari proyek lama.

## Domain Language

- Gunakan **identifikasi jenis sapi**, **hasil identifikasi**, **klasifikasi citra**, dan **tingkat keyakinan**.
- Gunakan branding **SapiKenal** secara konsisten untuk fitur dan dokumentasi baru.
- Jangan membingkai SapiKenal sebagai sistem diagnosis atau deteksi penyakit.
- Jika domain atau implementasi berubah, perbarui dokumentasi terkait dan `CONTEXT.md` secara konsisten.

## Root Commands

Jalankan dari root repository:

```bash
pnpm run backend:up
pnpm run backend:down
pnpm run backend:logs
pnpm run backend:test
pnpm run mobile:build
pnpm run mobile:deploy
pnpm run mobile:run
pnpm run mobile:test
pnpm run web:dev
pnpm run web:test
pnpm run test
pnpm run build
```

## Security and Generated Files

Jangan commit:

- `.env` atau `.env.*` selain `.env.example`
- `local.properties`
- credential, key, token, atau dump database produksi
- `node_modules/`, `.venv/`, `__pycache__/`, `.gradle/`, atau `build/`
- APK, AAB, dataset mentah, model besar, atau generated build output
