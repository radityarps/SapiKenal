# Mobile SapiKenal

Aplikasi Android menjalankan identifikasi jenis sapi melalui backend saat online
dan `lokal_fp32.tflite` saat offline/fallback. Kedua jalur memakai urutan kelas
`aceh`, `bali`, `limusin`, `madura`, `pasundan`, `po` dan mengembalikan hasil identifikasi,
tingkat keyakinan, seluruh skor, mode inferensi, serta versi model.

Preprocessing produksi mobile mengoreksi orientasi EXIF, melakukan resize
bilinear ke 224 × 224, dan membuat PNG lossless. `ModelPreprocessor` mendekode
PNG yang sama sebagai RGB dan menulis float32 mentah dalam rentang 0–255. Byte
PNG tersebut juga dikirim ke backend, sehingga kedua jalur memakai tensor input
yang identik. Model menjalankan rescaling internal.

Pengukuran perangkat pada 13 fixture nyata menghasilkan tensor input identik,
13/13 kelas pemenang sama, dan selisih skor maksimum `0.000002233688736`.
Lihat [`../model/parity.md`](../model/parity.md).

Artikel Panduan ditampilkan dari cache Room per locale. Saat halaman Panduan
dibuka, aplikasi langsung menampilkan cache (atau konten bawaan sebelum sync
pertama) lalu mengambil snapshot `id-ID`/`en-US` tanpa memblokir UI. Snapshot
valid mengganti seluruh locale dan mencatat keberhasilan secara atomik, termasuk
snapshot kosong; kegagalan jaringan, HTTP, parsing, atau validasi mempertahankan
cache terakhir.

Checklist rehearsal perangkat berada di
[`../../apps/mobile/SMOKE_TEST_CHECKLIST.md`](../../apps/mobile/SMOKE_TEST_CHECKLIST.md).
Build/unit test dan parity tidak menggantikan rehearsal kamera, galeri,
permission denial, online/offline/fallback, history, PDF, large text, dan
TalkBack.

## Build lokal dan Play Store

`pnpm run mobile:build` menghasilkan APK **debug** untuk pengembangan. APK ini
belum didistribusikan oleh Google Play, sehingga Play Protect dapat menampilkan
peringatan bahwa aplikasinya belum dikenal. Peringatan tersebut bukan kegagalan
build dan jangan diatasi dengan mematikan Play Protect pada perangkat pengguna.
Untuk pengujian tim, gunakan Internal App Sharing atau internal testing di Play
Console agar artefak didistribusikan melalui Google Play.

Rilis Play Store memakai Android App Bundle, target Android 16/API 36 sesuai
persyaratan aplikasi mobile baru dan update mulai 31 Agustus 2026, serta upload
key. Periksa kembali policy target API di Play Console sebelum setiap rilis:
<https://developer.android.com/google/play/requirements/target-sdk>.

1. Buat upload key satu kali dan simpan beserta password-nya di password manager:

   ```bash
   keytool -genkeypair -v -keystore apps/mobile/upload-keystore.jks \
     -alias upload -keyalg RSA -keysize 2048 -validity 10000
   ```

2. Isi konfigurasi rilis pada `apps/mobile/local.properties` yang diabaikan Git.
   Gunakan `apps/mobile/local.properties.example` sebagai daftar variabel.
   `RELEASE_API_BASE_URL` menerima HTTPS produksi atau HTTP LAN untuk build
   release yang diuji langsung, misalnya `http://192.168.18.36:8000/`. HTTP LAN
   tidak terenkripsi dan tidak boleh dipakai untuk distribusi Play Store;
   gunakan endpoint HTTPS publik sebelum mengunggah AAB.
3. Naikkan `VERSION_CODE` untuk setiap upload dan tetapkan `VERSION_NAME` yang
   akan ditampilkan kepada pengguna.
4. Bangun bundle bertanda tangan:

   ```bash
   pnpm run mobile:release
   ```

   Output berada di
   `apps/mobile/app/build/outputs/bundle/release/app-release.aab`. APK release
   untuk pengujian langsung dapat dibuat dengan `pnpm run mobile:release-apk`,
   tetapi Play Store menerima AAB.
5. Buat aplikasi dengan package `id.sapikenal.app` di Play Console, aktifkan
   [Play App Signing](https://developer.android.com/studio/publish/app-signing),
   lalu unggah AAB pertama ke internal testing. Lengkapi store
   listing, App access, Ads, Content rating, Target audience, Data safety,
   privacy policy, dan deklarasi permission sebelum mengirim production review.
6. Instal dari tautan internal testing, jalankan seluruh
   `SMOKE_TEST_CHECKLIST.md`, kemudian promosikan artefak yang sama ke closed,
   open, atau production track sesuai kebutuhan akun Play Console.

Keystore, password, `local.properties`, APK, dan AAB tidak boleh di-commit.
Cadangkan upload key dengan aman. Play App Signing melindungi app-signing key,
sementara upload key tetap diperlukan untuk mengunggah versi berikutnya.
