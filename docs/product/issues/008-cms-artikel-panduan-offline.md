# Bangun CMS Artikel Panduan dengan cache offline

## Tujuan

Memungkinkan administrator mengubah seluruh konten halaman Panduan melalui dashboard tanpa menghilangkan ketersediaan daftar dan detail artikel saat mobile offline.

## Dependensi

- Issue 006 untuk fondasi workflow revisi, review, aktivasi, dan audit profil.
- PRD [`../cms-panduan-offline.md`](../cms-panduan-offline.md).
- ADR [`../../architecture/0001-snapshot-artikel-panduan-offline.md`](../../architecture/0001-snapshot-artikel-panduan-offline.md).

## Scope

### Backend dan data

- Ganti model Profil Jenis menjadi Artikel Panduan dengan identitas stabil, locale, kategori, ikon, urutan, revisi, sumber, review, dan status publikasi.
- Pertahankan aturan satu revisi aktif per artikel-locale.
- Migrasikan Profil Jenis yang ada dan seed artikel hard-coded mobile; jangan mempertahankan dua sumber konten paralel.
- Sediakan endpoint admin untuk list, detail, create, revise, review, activate, dan deactivate.
- Sediakan endpoint publik snapshot lengkap yang hanya memuat revisi aktif untuk satu locale serta `snapshot_version` opaque.
- Terapkan batas ukuran/jumlah, kategori dan locale allowlist, validasi URL HTTP(S), transaksi, serta audit log.

### Web Admin

- Ubah menu Profil Jenis menjadi Artikel Panduan.
- Sediakan field `article_key`, locale, kategori, ikon, urutan, judul, ringkasan, isi, dan sumber.
- Pertahankan pemisahan perubahan isi, konfirmasi review, aktivasi, dan penonaktifan.
- Tampilkan pasangan locale dan tandai terjemahan yang belum dibuat atau belum aktif.
- Sediakan filter kategori, locale, dan status tanpa menambah editor kaya atau upload media.

### Mobile

- Tambahkan entity/DAO Room untuk snapshot Artikel Panduan dan metadata sync per locale.
- Ubah konten bawaan Indonesia dan Inggris menjadi snapshot seed dengan key stabil.
- Saat halaman Panduan dibuka, tampilkan data lokal segera lalu sinkronkan snapshot aktif tanpa memblokir UI.
- Terapkan snapshot tervalidasi dalam satu transaksi dan pertahankan cache lama pada semua jenis kegagalan sync.
- Catat keberhasilan sync locale walaupun respons valid berisi nol artikel agar konten yang ditarik tidak muncul kembali dari bundel.
- Gunakan sumber lokal yang sama untuk daftar, pencarian, filter, dan detail.
- Saat locale berubah, gunakan cache locale tujuan atau snapshot bawaan locale tersebut, lalu sinkronkan.

### Dokumentasi

- Perbarui dokumentasi API dan mobile dengan kontrak snapshot, fallback, serta batas stale content.
- Perbarui `CONTEXT.md` bila implementasi mengubah istilah domain yang telah disepakati.

## Bukan Scope

- Markdown, HTML, WYSIWYG, upload gambar, atau object storage.
- Tag bebas, komentar, analitik pembaca, push update, atau sync periodik WorkManager.
- Publikasi serentak satu paket artikel.

## Kriteria penerimaan

- [ ] Administrator dapat mengelola semua kategori Artikel Panduan pada dashboard.
- [ ] Setiap perubahan isi menghasilkan draft baru dan membatalkan review revisi tersebut.
- [ ] Hanya revisi dengan sumber valid dan review eksplisit yang dapat diaktifkan.
- [ ] Endpoint publik tidak membocorkan draft, metadata admin, atau revisi nonaktif.
- [ ] Snapshot API lengkap dan deterministik untuk `id-ID` serta `en-US`.
- [ ] Instalasi baru tanpa jaringan menampilkan artikel bawaan untuk locale aktif.
- [ ] Setelah sync sukses, daftar dan detail tetap tersedia dengan konten terbaru ketika jaringan dimatikan.
- [ ] Timeout, HTTP error, payload terlalu besar, kategori/locale salah, atau parsing error tidak mengganti cache valid.
- [ ] Respons sukses kosong menarik semua artikel CMS locale dan tidak mengaktifkan kembali seed.
- [ ] Penonaktifan artikel menghapusnya dari mobile setelah sync sukses berikutnya.
- [ ] Pencarian dan filter kategori bekerja terhadap data lokal tanpa jaringan.
- [ ] Profil Jenis lama dan artikel hard-coded termigrasi; tidak ada dua CMS atau endpoint publik paralel.
- [ ] Audit log mencatat lifecycle artikel dengan actor dan resource yang benar.
- [ ] Test backend, migration, web, dan mobile lulus.

## Skenario verifikasi minimum

1. Instal aplikasi tanpa jaringan dan buka daftar serta detail Panduan untuk kedua locale.
2. Aktifkan revisi artikel dari dashboard, buka Panduan saat online, lalu matikan jaringan dan pastikan revisi baru tetap terbaca.
3. Simulasikan respons rusak setelah cache tersedia dan pastikan cache lama tidak berubah.
4. Nonaktifkan artikel, lakukan sync sukses, tutup/buka aplikasi saat offline, dan pastikan artikel tidak kembali.
5. Aktifkan artikel Indonesia tanpa Inggris dan pastikan setiap locale memakai snapshot/cache sendiri tanpa mencampur bahasa.

## Verifikasi

```bash
pnpm run backend:test
pnpm run mobile:test
pnpm run web:test
pnpm run web:check
pnpm run build
git diff --check
```
