# Migrasikan Web Admin dan profil jenis

## Tujuan

Mengubah Web Admin dari pelaporan/konten penyakit menjadi pengelolaan hasil identifikasi dan profil empat jenis sapi.

## Dependensi

- Issue 002.
- Issue 003.

## Scope

- Ganti kartu dashboard, distribusi, filter, tabel, detail skor, dan empty state menjadi empat jenis sapi.
- Hapus statistik dan filter penolakan `non_cattle` yang berasal dari model lama.
- Ganti modul `diseases` dan entitas konten penyakit menjadi profil jenis.
- Sediakan field kelebihan dan kekurangan yang jelas untuk setiap profil.
- Pertahankan workflow draft/aktif/nonaktif dan audit log jika masih berguna.
- Perbarui route backend admin/public, schema, DB table, Web Admin, dan test secara terkoordinasi.
- Pastikan klaim profil belum dipublikasikan sebelum kontennya ditinjau dan memiliki sumber yang layak.

## Kriteria penerimaan

- [x] Dashboard mendistribusikan hasil Bali, Brahman, Brangus, dan Limusin.
- [x] Filter dan detail menampilkan empat skor dengan label benar.
- [x] Administrator dapat membuat, mengubah, mengaktifkan, dan menonaktifkan profil jenis.
- [x] Profil aktif tersedia bagi mobile melalui endpoint publik.
- [x] Audit log memakai istilah profil jenis, bukan penyakit.
- [x] Tidak ada statistik klinis atau penolakan non-sapi yang tersisa.
- [x] `pnpm run web:test` dan backend test lulus.

## Verifikasi

```bash
pnpm run backend:build
pnpm run backend:test
pnpm run web:test
pnpm run web:check
pnpm run build
```
