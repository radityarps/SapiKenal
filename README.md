# SapiKenal

Fondasi aplikasi untuk mengidentifikasi jenis sapi dari citra. Branding aplikasi dan identifier teknis utama telah menggunakan nama SapiKenal.

> Status: migrasi domain masih berlangsung. Alur klasifikasi penyakit dan artefak model lama masih dipertahankan sementara sebagai fondasi teknis hingga dataset serta model identifikasi jenis sapi tersedia.

## Struktur Repository

```text
SapiKenal/
├── apps/
│   ├── backend/          # Backend FastAPI
│   ├── mobile/           # Aplikasi Android Kotlin
│   └── web/              # Web admin SvelteKit
├── docs/
│   ├── architecture/     # Arsitektur dan keputusan teknis
│   ├── dataset/          # Dataset dan proses pengolahannya
│   ├── model/            # Pelatihan, evaluasi, dan versi model
│   ├── api/              # Kontrak dan panduan API
│   └── mobile/           # Dokumentasi aplikasi Android
├── scripts/              # Script pengembangan yang masih digunakan
├── package.json          # Perintah root
└── pnpm-workspace.yaml   # Konfigurasi workspace
```

Lihat [`docs/README.md`](docs/README.md) untuk indeks dokumentasi.

## Prasyarat

- Node.js 18+
- pnpm 10+
- Docker 24+
- Android SDK API 24+
- `adb` untuk memasang dan menjalankan aplikasi pada perangkat/emulator

## Perintah Root

```bash
pnpm run backend:up      # Build dan jalankan backend
pnpm run backend:down    # Hentikan backend
pnpm run backend:logs    # Tampilkan log backend
pnpm run backend:test    # Jalankan test backend
pnpm run backend:smoke   # Reset database dev, load best.keras, and smoke-test /api/predict

pnpm run mobile:build    # Build APK debug
pnpm run mobile:deploy   # Build dan install APK
pnpm run mobile:run      # Build, install, dan jalankan aplikasi
pnpm run mobile:test     # Jalankan unit test Android
```

Backend lokal tersedia di `http://localhost:8000`; dokumentasi OpenAPI tersedia di `http://localhost:8000/docs`.

## Konfigurasi Mobile

Salin konfigurasi lokal sebelum build:

```bash
cp apps/mobile/local.properties.example apps/mobile/local.properties
```

Atur `API_BASE_URL` di `apps/mobile/local.properties`. Berkas tersebut bersifat lokal dan tidak boleh di-commit.

## Dokumentasi

Dokumentasi baru hanya disimpan berdasarkan kebutuhan implementasi:

- [`docs/architecture/`](docs/architecture/)
- [`docs/dataset/`](docs/dataset/)
- [`docs/model/`](docs/model/)
- [`docs/api/`](docs/api/)
- [`docs/mobile/`](docs/mobile/)

Dataset mentah, artefak model besar, credential, `.env`, `local.properties`, dan output build tidak boleh di-commit.

## Lisensi

Lihat [LICENSE](LICENSE).
