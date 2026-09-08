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
      "bali": 0.91,
      "brahman": 0.04,
      "brangus": 0.03,
      "limusin": 0.02
    }
  },
  "model_info": {"version": "sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32"},
  "processing_time_ms": 120,
  "preprocessing_time_ms": 20,
  "inference_time_ms": 100
}
```

Urutan skor wajib `bali`, `brahman`, `brangus`, `limusin`. Backend memproses
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
