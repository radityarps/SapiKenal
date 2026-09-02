# PRD — Identifikasi Jenis Sapi

## Ringkasan

SapiKenal mengganti fondasi klasifikasi penyakit dengan identifikasi empat jenis sapi dari citra: Bali, Brahman, Brangus, dan Limusin. Rilis pertama harus menyediakan inferensi online melalui model Keras dan inferensi offline melalui model TFLite dengan kontrak kelas dan preprocessing yang sama.

## Tujuan

- Pengguna dapat memilih atau mengambil citra dan memperoleh satu hasil identifikasi jenis sapi beserta tingkat keyakinannya.
- Hasil online dan offline menggunakan urutan kelas yang sama dan memberikan hasil yang sepadan untuk citra uji yang sama.
- Riwayat, laporan, Web Admin, API, dan dokumentasi memakai bahasa identifikasi jenis sapi.
- Pengguna dapat membaca profil kelebihan dan kekurangan setiap jenis yang didukung.

## Bukan Tujuan

- Memastikan bahwa objek pada citra adalah sapi.
- Menolak citra non-sapi atau jenis sapi di luar empat kelas.
- Mengidentifikasi penyakit, kondisi kesehatan, atau identitas individual sapi.
- Mempertahankan atau memigrasikan data hasil klasifikasi penyakit lama.
- Menambah jenis sapi di luar Bali, Brahman, Brangus, dan Limusin pada rilis ini.

## Pengguna dan Kebutuhan

### Pengguna aplikasi

- Mengambil foto atau memilih citra dari galeri.
- Melihat satu jenis sapi yang dipilih model dan tingkat keyakinannya.
- Tetap dapat menggunakan identifikasi saat offline.
- Meninjau riwayat dan membagikan laporan hasil identifikasi.
- Membaca kelebihan dan kekurangan jenis sapi yang didukung.

### Administrator

- Melihat distribusi hasil berdasarkan empat jenis sapi.
- Menelusuri detail hasil dan skor setiap kelas.
- Mengelola profil jenis sapi.
- Mendaftarkan dan mengaktifkan model yang memenuhi kontrak kelas.

## Kontrak Model

Urutan kelas berikut bersifat final dan mengikat seluruh sistem:

| Indeks | Label kanonik | Label tampilan Indonesia |
| --- | --- | --- |
| 0 | `bali` | Bali |
| 1 | `brahman` | Brahman |
| 2 | `brangus` | Brangus |
| 3 | `limusin` | Limusin |

Artefak awal:

- Backend: `apps/backend/model/best.keras`
- Mobile: `apps/mobile/app/src/main/assets/jenis_fp32.tflite`
- Sumber urutan kelas: `apps/backend/model/class_names.json`

Kedua model menerima citra RGB `224 × 224` dan menghasilkan empat probabilitas. Preprocessing, urutan kanal, resize, dan rentang nilai masukan harus terdokumentasi dan diuji sebagai satu kontrak.

## Perilaku Produk

1. Sistem memproses setiap citra yang berhasil didekode.
2. Sistem memilih kelas dengan skor tertinggi.
3. Sistem menampilkan nama jenis dan tingkat keyakinan, termasuk ketika nilainya rendah.
4. Sistem tidak menampilkan klaim bahwa citra telah divalidasi sebagai sapi.
5. Sistem tidak memberi peringatan khusus untuk tingkat keyakinan rendah pada rilis ini.
6. Riwayat menyimpan hasil teratas, tingkat keyakinan, seluruh skor kelas, mode inferensi, versi model, dan metadata yang telah ada serta masih relevan.
7. Profil jenis menjelaskan kelebihan dan kekurangan tanpa mengubah hasil model menjadi rekomendasi pembelian, pembiakan, atau kesehatan.

## Kontrak API Target

Respons sukses menggunakan istilah domain netral dan tidak membawa nama penyakit:

```json
{
  "status": "success",
  "prediction": {
    "predicted_class": "bali",
    "confidence": 0.91,
    "scores": {
      "bali": 0.91,
      "brahman": 0.04,
      "brangus": 0.03,
      "limusin": 0.02
    }
  },
  "model_info": {
    "version": "..."
  },
  "processing_time_ms": 120,
  "preprocessing_time_ms": 20,
  "inference_time_ms": 100
}
```

Nama versi model ditetapkan saat implementasi setelah metadata training/export dikonfirmasi. Respons tidak memiliki jalur `NON_CATTLE_IMAGE`.

## Data dan Migrasi

- Database pengembangan lama boleh di-reset; hasil penyakit tidak dimigrasikan.
- Schema baru tidak memakai kolom skor penyakit.
- Skor disimpan sebagai objek yang mempertahankan label kanonik agar kontrak tidak tersebar menjadi kolom penyakit atau jenis tertentu.
- Seed, fixture, dan dashboard lama diganti dengan data empat jenis sapi.
- Artefak model lama hanya dihapus dari working tree setelah perubahan tersebut dikonfirmasi sebagai bagian issue aktivasi artefak.

## Profil Jenis

Setiap profil minimal memiliki:

- label jenis yang sesuai kontrak model;
- nama tampilan;
- ringkasan;
- kelebihan;
- kekurangan;
- status publikasi dan locale jika pengelolaan konten lama dipertahankan.

Isi profil harus dapat ditinjau secara terpisah dari implementasi model. Klaim faktual tentang karakteristik jenis memerlukan sumber yang layak sebelum dipublikasikan.

## Persyaratan Nonfungsional

- **Parity:** Keras dan TFLite memilih kelas yang sama pada corpus parity yang disepakati; toleransi selisih skor dicatat oleh implementasi setelah baseline diukur.
- **Offline:** identifikasi TFLite berjalan tanpa jaringan.
- **Kegagalan aman:** model dengan bentuk tensor, tipe data, atau urutan kelas yang salah tidak boleh diaktifkan.
- **Privasi:** tidak ada perubahan yang memperluas pengumpulan citra atau lokasi tanpa persetujuan pengguna.
- **Aksesibilitas:** hasil tidak dibedakan hanya dengan warna dan seluruh teks utama tetap dapat dibaca pembaca layar.
- **Bahasa:** UI Indonesia dan Inggris tidak menyebut diagnosis atau deteksi penyakit.

## Kriteria Penerimaan Rilis

- Model Keras dan TFLite dapat memproses fixture nyata melalui jalur produksi masing-masing.
- Kedua mode mengembalikan tepat empat skor dengan urutan label kanonik.
- Aplikasi menampilkan Bali, Brahman, Brangus, atau Limusin serta tingkat keyakinan.
- Tidak ada jalur runtime atau UI yang memetakan kelas ke PMK, LSD, sehat, atau non-sapi.
- API, database baru, sinkronisasi riwayat, PDF, dashboard, filter, dan detail hasil memakai kontrak jenis sapi.
- Profil kelebihan dan kekurangan tersedia untuk keempat jenis.
- Test backend, mobile, web, dan parity lulus.
- Dokumentasi model mencatat artefak, checksum, input/output, preprocessing, class order, dan keterbatasan.

## Risiko

- Class order yang salah menghasilkan label yang salah walaupun inferensi teknis berhasil.
- Perbedaan preprocessing Android dan backend dapat menghasilkan hasil berbeda.
- Karena tidak ada validator sapi, citra apa pun tetap mendapat salah satu dari empat label; batasan ini harus dinyatakan jelas.
- Reset database menghapus data pengembangan lama dan harus dibatasi pada lingkungan nonproduksi.
- Profil kelebihan/kekurangan dapat terdengar seperti rekomendasi mutlak jika tidak ditulis secara kontekstual.

## Backlog

Implementasi dipecah dalam issue pada [`issues/`](issues/README.md). Urutan kritis:

1. kontrak dan validasi artefak;
2. backend dan schema data;
3. mobile offline/online;
4. UI, laporan, Web Admin, dan profil jenis;
5. parity, pembersihan istilah lama, dan dokumentasi akhir.
