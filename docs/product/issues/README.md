# Backlog Migrasi Identifikasi Jenis Sapi

Issue files ini menguraikan implementasi [PRD Identifikasi Jenis Sapi](../identifikasi-jenis-sapi.md). Nomor menunjukkan urutan yang disarankan, bukan nomor GitHub Issue.

| Urutan | Issue | Dependensi |
| --- | --- | --- |
| 1 | [Tetapkan dan validasi kontrak model](001-kontrak-model.md) | — |
| 2 | [Migrasikan inferensi dan API backend](002-backend-inference-api.md) | 001 |
| 3 | [Reset schema hasil identifikasi](003-schema-dan-riwayat.md) | 001 |
| 4 | [Migrasikan inferensi mobile](004-mobile-inference.md) | 001, 002 |
| 5 | [Migrasikan pengalaman mobile dan laporan](005-mobile-ui-dan-laporan.md) | 003, 004 |
| 6 | [Migrasikan Web Admin dan profil jenis](006-web-admin-dan-profil.md) | 002, 003 |
| 7 | [Verifikasi parity dan selesaikan migrasi domain](007-parity-dan-cleanup.md) | 002–006 |
