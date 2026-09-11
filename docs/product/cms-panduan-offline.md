# PRD — CMS Artikel Panduan Offline

## Ringkasan

SapiKenal menyediakan satu CMS Artikel Panduan agar administrator dapat mengubah seluruh konten pada halaman Panduan mobile, termasuk panduan penggunaan aplikasi dan Profil Jenis. Aplikasi menampilkan data lokal terlebih dahulu, menyinkronkan artikel aktif saat halaman Panduan dibuka, dan tetap menyediakan konten ketika tidak ada jaringan.

## Tujuan

- Administrator dapat membuat, merevisi, meninjau, menerbitkan, dan menonaktifkan Artikel Panduan melalui dashboard.
- Pengguna memperoleh artikel aktif terbaru tanpa memperbarui aplikasi.
- Halaman Panduan langsung tersedia saat offline melalui cache terakhir atau konten bawaan APK.
- Konten Indonesia dan Inggris dikelola dengan identitas artikel yang sama.
- Profil Jenis memakai alur konten yang sama dengan panduan penggunaan aplikasi.

## Bukan Tujuan

- Editor kaya, HTML, Markdown, unggahan gambar, atau pustaka media.
- Komentar, akun penulis publik, tag bebas, rekomendasi personal, atau analitik pembaca.
- Sinkronisasi periodik di latar belakang atau push notification perubahan konten.
- Diagnosis, saran kesehatan, atau rekomendasi mutlak tentang jenis sapi.
- Menambah jenis sapi di luar kontrak model yang berlaku.

## Pengguna dan Kebutuhan

### Pengguna aplikasi

- Membuka daftar dan detail Artikel Panduan tanpa menunggu jaringan.
- Mencari dan memfilter artikel berdasarkan kategori.
- Membaca konten dalam locale aplikasi.
- Tetap melihat cache terakhir ketika sinkronisasi gagal.

### Administrator

- Mengelola panduan penggunaan aplikasi dan Profil Jenis dari dashboard yang sama.
- Menyimpan perubahan sebagai draft tanpa langsung mengubah konten publik.
- Meninjau isi dan sumber sebelum publikasi.
- Mengatur kategori, ikon, urutan tampil, locale, dan status artikel.
- Melihat tindakan pengelolaan konten pada audit log.

## Model Konten

Setiap **Artikel Panduan** memiliki identitas stabil yang tidak berubah antar-revisi dan locale. Isinya minimal mencakup:

- `article_key`: kunci stabil dan unik untuk memasangkan terjemahan;
- `locale`: `id-ID` atau `en-US`;
- `category`: `app_usage`, `bali`, `brahman`, `brangus`, atau `limusin`;
- `icon`: ikon teks yang didukung UI;
- `sort_order`: bilangan urutan dalam kategori;
- `title`, `summary`, dan `body`: teks terstruktur tanpa HTML/Markdown;
- `sources`: satu atau lebih URL sumber;
- `revision`: nomor revisi yang bertambah;
- status `draft`, `active`, atau `inactive`;
- tanda bahwa isi dan sumber telah ditinjau.

Artikel pada kategori jenis sapi adalah **Profil Jenis**. Kategori Bali, Brahman, Brangus, dan Limusin harus sesuai kontrak Jenis Sapi. Pasangan terjemahan berbagi `article_key`, tetapi masing-masing memiliki revisi, review, dan status publikasi sendiri.

## Alur Publikasi

1. Administrator membuat atau merevisi satu artikel.
2. Perubahan disimpan sebagai revisi `draft` dan membatalkan tanda review untuk revisi tersebut.
3. Administrator meninjau isi serta sumber secara terpisah.
4. Hanya revisi yang telah ditinjau dan memiliki sumber valid yang dapat diaktifkan.
5. Aktivasi menggantikan revisi aktif artikel-locale yang sama secara atomik.
6. Penonaktifan mengeluarkan artikel dari snapshot publik berikutnya.

Tidak ada publikasi massal pada rilis pertama; konsistensi dijaga per artikel-locale.

## Distribusi dan Perilaku Offline

- APK membawa snapshot awal artikel untuk `id-ID` dan `en-US`.
- Saat halaman Panduan dibuka, mobile segera membaca cache lokal. Jika cache untuk locale belum ada, mobile membaca snapshot bawaan.
- Mobile kemudian meminta snapshot semua artikel aktif untuk locale aplikasi.
- Respons sukses divalidasi dan mengganti cache locale secara atomik; daftar kosong adalah snapshot valid dan menarik semua artikel CMS untuk locale tersebut.
- Kegagalan jaringan, HTTP, parsing, atau validasi tidak menghapus cache yang masih valid.
- Setelah sinkronisasi sukses, artikel yang tidak lagi ada dalam snapshot server tidak ditampilkan. Sebelum sinkronisasi sukses, salinan cache lama tetap tersedia saat offline.
- Detail artikel harus dibaca dari sumber lokal yang sama dengan daftar, bukan mengambil ulang dari jaringan.
- Sinkronisasi tidak memblokir tampilan lokal dan tidak memerlukan WorkManager.

Konten bawaan adalah jaring pengaman instalasi baru, bukan salinan yang menang atas cache. Untuk mencegah artikel yang telah ditarik muncul kembali setelah cache valid menjadi kosong, mobile harus menyimpan status bahwa sinkronisasi locale pernah berhasil.

## Kontrak API Target

Endpoint publik mengembalikan snapshot lengkap untuk satu locale, hanya berisi revisi aktif. Respons memiliki penanda versi snapshot yang berubah ketika komposisi atau revisi aktif berubah.

```json
{
  "status": "success",
  "locale": "id-ID",
  "snapshot_version": "opaque-version",
  "items": [
    {
      "article_key": "profil-bali",
      "category": "bali",
      "icon": "🐄",
      "sort_order": 10,
      "title": "Profil Sapi Bali",
      "summary": "...",
      "body": "...",
      "sources": ["https://example.org/source"],
      "revision": 3
    }
  ]
}
```

`article_key` pada contoh bersifat ilustratif; implementasi harus memakai slug aman dan stabil. API publik tidak mengirim draft, metadata administrator, atau status review.

## Migrasi

- Data dan workflow `BreedProfile` yang ada dimigrasikan ke Artikel Panduan, lalu endpoint serta menu Profil lama dipensiunkan setelah consumer berpindah.
- `canonical_key` profil lama dipetakan ke kategori jenis yang sama.
- Field `display_name`, `summary`, `strengths`, `limitations`, dan `disclaimer` disusun menjadi `title`, `summary`, dan `body` tanpa kehilangan sumber atau histori revisi yang masih relevan.
- Artikel hard-coded mobile dipindahkan menjadi snapshot bawaan dengan `article_key` stabil untuk kedua locale.
- Migrasi harus idempoten pada data yang memenuhi constraint dan gagal jelas jika menemukan key/locale yang tidak didukung.

## Persyaratan Nonfungsional

- **Offline-first:** daftar dan detail dapat digunakan tanpa jaringan sejak instalasi pertama.
- **Konsistensi cache:** snapshot baru diterapkan dalam satu transaksi; cache sebelumnya dipertahankan bila sinkronisasi gagal.
- **Keamanan konten:** teks dirender sebagai teks biasa; URL sumber hanya menerima HTTP(S); ukuran setiap field dan jumlah artikel dibatasi di trust boundary.
- **Aksesibilitas:** ikon bukan satu-satunya pembeda kategori; judul, kategori, dan isi dapat dibaca pembaca layar.
- **Lokalisasi:** mobile meminta locale aktif; bila locale CMS belum pernah sukses disinkronkan, gunakan snapshot bawaan locale tersebut.
- **Observabilitas:** kegagalan sync dapat didiagnosis tanpa mencatat isi sensitif atau credential; waktu sync sukses terakhir dapat ditampilkan bila UI membutuhkannya.
- **Performa:** data lokal ditampilkan tanpa menunggu request; pencarian tetap dilakukan secara lokal.

## Kriteria Penerimaan

- Administrator dapat mengelola seluruh kategori Artikel Panduan melalui dashboard.
- Perubahan konten membuat revisi draft dan tidak tampil publik sebelum review serta aktivasi.
- Endpoint publik hanya mengembalikan snapshot revisi aktif untuk locale yang diminta.
- Instalasi baru tanpa jaringan menampilkan snapshot bawaan Indonesia atau Inggris sesuai locale.
- Setelah sync sukses, mode offline menampilkan snapshot server terakhir.
- Sync gagal atau respons tidak valid tidak mengosongkan konten lokal.
- Artikel yang dinonaktifkan hilang setelah sync sukses dan tidak muncul kembali dari bundel pada pembukaan berikutnya.
- Daftar, pencarian, filter kategori, dan detail memakai data lokal yang konsisten.
- Profil Jenis lama dan artikel hard-coded telah dimigrasikan tanpa mempertahankan dua CMS paralel.
- Audit log mencatat pembuatan, revisi, review, aktivasi, dan penonaktifan artikel.
- Test backend, mobile, web, migrasi, dan skenario offline lulus.

## Risiko

- Penggantian seluruh snapshot dapat menarik artikel secara tidak sengaja bila endpoint menghasilkan data parsial; karena itu hanya respons lengkap dan valid yang boleh diterapkan.
- Locale yang diterbitkan tidak serempak dapat menghasilkan isi berbeda antarbahasa; status dikelola per artikel-locale dan dashboard perlu memperlihatkan pasangan yang belum lengkap.
- Migrasi Profil Jenis dapat mengubah struktur narasi; hasil migrasi wajib kembali berstatus draft bila penyusunan body tidak dapat dipastikan aman.
- Konten cache dapat tetap usang selama perangkat offline; penarikan berlaku setelah sinkronisasi sukses, bukan secara real-time.
