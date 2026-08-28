# SapiKenal

SapiKenal mengidentifikasi jenis atau ras sapi dari citra. Proyek ini tidak mengidentifikasi penyakit dan tidak menetapkan identitas individual sapi.

## Language

**Jenis Sapi**:
Kategori ras atau kelompok sapi yang menjadi target klasifikasi model.
_Avoid_: penyakit sapi, kondisi kesehatan

**Citra Sapi**:
Foto yang menjadi masukan proses identifikasi jenis sapi.
_Avoid_: rekam medis, bukti diagnosis

**Hasil Identifikasi**:
Keluaran model berupa kandidat jenis sapi dan tingkat keyakinannya.
_Avoid_: diagnosis, hasil pemeriksaan kesehatan

**Tingkat Keyakinan**:
Skor numerik yang menunjukkan keyakinan relatif model terhadap hasil identifikasi.
_Avoid_: kepastian, jaminan akurasi

**Dataset Sapi**:
Kumpulan citra sapi berlabel jenis yang digunakan untuk pelatihan, validasi, atau pengujian model.
_Avoid_: dataset penyakit

**Model Identifikasi**:
Model klasifikasi citra yang memetakan citra sapi ke salah satu jenis sapi yang didukung.
_Avoid_: model diagnosis penyakit
