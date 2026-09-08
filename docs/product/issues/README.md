# Backlog Produk SapiKenal

Issue files ini menguraikan implementasi [PRD Identifikasi Jenis Sapi](../identifikasi-jenis-sapi.md) dan [PRD CMS Artikel Panduan Offline](../cms-panduan-offline.md). Nomor menunjukkan urutan yang disarankan, bukan nomor GitHub Issue.

| Urutan | Issue | Status implementasi | Sudah di-commit | Dependensi |
| --- | --- | --- | --- | --- |
| 1 | [Tetapkan dan validasi kontrak model](001-kontrak-model.md) | Selesai | Ya (`9db1709`) | — |
| 2 | [Migrasikan inferensi dan API backend](002-backend-inference-api.md) | Selesai | Ya (`9db1709`) | 001 |
| 3 | [Reset schema hasil identifikasi](003-schema-dan-riwayat.md) | Selesai | Ya | 001 |
| 4 | [Migrasikan inferensi mobile](004-mobile-inference.md) | Selesai; verifikasi perangkat tertunda | Ya | 001, 002 |
| 5 | [Migrasikan pengalaman mobile dan laporan](005-mobile-ui-dan-laporan.md) | Implementasi selesai; verifikasi manual perangkat tertunda | Ya (`6ca4469`) | 003, 004 |
| 6 | [Migrasikan Web Admin dan profil jenis](006-web-admin-dan-profil.md) | Selesai | Ya (`4c90d47`) | 002, 003 |
| 7 | [Verifikasi parity dan selesaikan migrasi domain](007-parity-dan-cleanup.md) | Implementasi selesai; verifikasi akhir berjalan | Tidak | 002–006 |
| 8 | [Bangun CMS Artikel Panduan dengan cache offline](008-cms-artikel-panduan-offline.md) | Belum dimulai | Tidak | 006 |

Status mencatat penyelesaian scope issue secara keseluruhan. Perubahan parsial yang menjadi fondasi issue berikutnya tidak mengubah status issue tersebut menjadi selesai.
