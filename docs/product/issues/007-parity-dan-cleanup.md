# Verifikasi parity dan selesaikan migrasi domain

## Tujuan

Membuktikan bahwa mode online/offline memenuhi kontrak yang sama dan menghapus sisa asumsi penyakit sebelum rilis.

## Dependensi

- Issue 002–006.

## Scope

- Buat corpus parity kecil yang legal disimpan atau script yang menunjuk fixture lokal non-Git.
- Jalankan citra yang sama melalui Keras dan TFLite dengan preprocessing produksi.
- Catat kesamaan kelas pemenang dan baseline selisih skor; tetapkan toleransi berdasarkan hasil ukur, bukan tebakan.
- Tambahkan regression check parity yang runnable.
- Scan source, test, resource, docs, migration baru, dan UI untuk istilah/kontrak penyakit lama.
- Perbarui README, dokumentasi API/mobile/model, dan status migrasi.
- Verifikasi artefak besar, dataset mentah, database runtime, credential, dan build output tidak ikut commit.

## Kriteria penerimaan

- [x] Semua 13 fixture parity memilih kelas yang sama pada Keras dan TFLite; bukti dan baseline tercatat di [`../../model/parity.md`](../../model/parity.md).
- [x] Toleransi skor didokumentasikan dari baseline terukur.
- [x] Tidak ada referensi runtime ke model penyakit lama.
- [x] Tidak ada kontrak `disease_class`, kelas PMK/LSD/sehat/non-sapi, atau konten penyakit pada fitur baru. Referensi tersisa terbatas pada migration immutable, reset/migration safety, negative contract tests, dan histori issue.
- [x] README tidak lagi menyatakan bahwa model identifikasi belum tersedia.
- [ ] Backend, mobile, web, build, dan diagnostics lulus.
- [ ] Working tree hanya berisi artefak yang memang disetujui untuk commit.

## Status verifikasi

Implementasi regression check dan audit domain selesai. Preprocessing
backend/Android menghasilkan tensor identik pada seluruh corpus, 13/13 winner
sama, dan baseline terukur diterima. Proyek tetap controlled prototype/MVP,
bukan production-ready, sampai rehearsal manual/perangkat dan operasional pada
bagian batasan selesai.

## Verifikasi

```bash
pnpm run test
pnpm run build
git diff --check
```

Tambahkan perintah parity dari issue 001 ke rangkaian verifikasi akhir.
