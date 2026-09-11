# SapiKenal

SapiKenal mengidentifikasi jenis sapi dari citra. Proyek ini tidak mengidentifikasi penyakit, memvalidasi bahwa citra memuat sapi, atau menetapkan identitas individual sapi.

## Language

**Jenis Sapi**:
Kategori sapi yang menjadi target klasifikasi model. Jenis sapi yang didukung adalah Aceh, Bali, Limusin, Madura, Pasundan, dan PO.
_Avoid_: ras sapi, penyakit sapi, kondisi kesehatan

**Citra Identifikasi**:
Foto yang menjadi masukan proses identifikasi jenis sapi. Citra ini tidak dianggap telah tervalidasi memuat sapi.
_Avoid_: citra sapi, rekam medis, bukti diagnosis

**Hasil Identifikasi**:
Keluaran model berupa satu jenis sapi dengan tingkat keyakinannya. Hasil selalu memilih salah satu jenis yang didukung dan tidak membuktikan bahwa objek pada citra adalah sapi.
_Avoid_: diagnosis, validasi sapi, hasil pemeriksaan kesehatan

**Tingkat Keyakinan**:
Skor numerik yang menunjukkan keyakinan relatif model terhadap hasil identifikasi.
_Avoid_: kepastian, jaminan akurasi

**Dataset Sapi**:
Kumpulan citra sapi berlabel jenis yang digunakan untuk pelatihan, validasi, atau pengujian model.
_Avoid_: dataset penyakit

**Model Identifikasi**:
Model klasifikasi citra yang memetakan citra identifikasi ke salah satu jenis sapi yang didukung.
_Avoid_: model validasi sapi, model diagnosis penyakit

**Artikel Panduan**:
Konten edukatif yang dapat dibaca pengguna, mencakup penggunaan aplikasi dan informasi tentang jenis sapi yang didukung.
_Avoid_: blog, artikel penyakit, saran diagnosis

**Profil Jenis**:
Artikel Panduan yang membahas karakteristik, kelebihan, dan kekurangan satu jenis sapi yang didukung.
_Avoid_: entitas profil terpisah, panduan penyakit, rekomendasi mutlak
