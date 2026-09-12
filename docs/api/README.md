# API SapiKenal

Backend menyediakan OpenAPI di `/docs`. Jalur inferensi utama adalah
`POST /api/predict` dengan unggahan JPEG, PNG, atau WebP. Respons sukses memakai
kontrak berikut:

```json
{
  "status": "success",
  "prediction": {
    "predicted_class": "bali",
    "confidence": 0.91,
    "scores": {
      "aceh": 0.02,
      "bali": 0.91,
      "limusin": 0.02,
      "madura": 0.02,
      "pasundan": 0.02,
      "po": 0.01
    }
  },
  "model_info": {"version": "sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32"},
  "processing_time_ms": 120,
  "preprocessing_time_ms": 20,
  "inference_time_ms": 100
}
```

Urutan skor wajib `aceh`, `bali`, `limusin`, `madura`, `pasundan`, `po`. Backend memproses
setiap citra yang berhasil didekode dan tidak memvalidasi bahwa citra memuat
sapi. Model yang belum tersedia menghasilkan HTTP 503; format atau data citra
yang tidak valid menghasilkan HTTP 422.

Smoke model nyata memerlukan fixture lokal non-Git:

```bash
pnpm run backend:smoke -- --image /path/to/fixture.jpg
```

Perintah tersebut menjalankan `backend:dev` dan **menghapus data SQLite serta
volume development** sebelum menyalakan backend. Gunakan hanya terhadap
lingkungan development lokal; untuk backend yang sudah berjalan, panggil
`apps/backend/scripts/smoke_production.py` secara langsung.

Smoke tersebut membuktikan bahwa artefak Keras dapat melayani satu permintaan,
bukan production readiness atau akurasi model. Status parity Keras–TFLite ada
di [`../model/parity.md`](../model/parity.md).

## Artikel Panduan

Dashboard mengelola Artikel Panduan melalui `/api/admin/articles`; perubahan isi
membuat revisi draft yang harus ditinjau sebelum diaktifkan. Response admin
memisahkan `publication_status` (status publikasi artikel), `revision.status`
(status editorial revisi terbaru), dan `active_revision` (revisi publik saat ini
atau `null`). Karena itu artikel dengan publikasi aktif tetap dapat mempunyai
revisi terbaru berstatus draft. Listing menerima filter `publication_status` dan
`revision_status` secara terpisah; filter dapat digabung dengan `category`.

Endpoint publik `GET /api/content/articles`
mengembalikan snapshot lengkap revisi aktif (Bahasa Indonesia), `snapshot_version` deterministik,
dan tidak mengirim metadata admin. Snapshot sukses kosong adalah valid dan
berarti semua artikel telah ditarik.

Setelah migration, jalankan bootstrap admin dan draft Artikel Panduan secara
eksplisit dari `apps/backend`:

```bash
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='password-kuat' \
  python -m scripts.seed_admin
```

Seeder membuat Artikel Panduan sebagai draft yang belum ditinjau dan tidak
mengaktifkan konten. Administrator harus melengkapi sumber, meninjau isi serta
sumber, lalu mengaktifkan revisi melalui dashboard. Menjalankan command kembali
bersifat idempoten dan tidak menimpa artikel atau revisi yang telah diedit admin.
Alur development `backend:dev` tetap menjalankan seeder ini; deployment
non-development harus menjalankannya sebagai langkah eksplisit setelah migration,
bukan sebagai auto-seed tersembunyi saat backend dimulai.
