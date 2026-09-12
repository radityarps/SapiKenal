# SapiKenal

Controlled prototype/MVP untuk mengidentifikasi jenis sapi dari citra. Backend Keras dan aplikasi Android TFLite memakai artefak identifikasi enam jenis sapi (Aceh, Bali, Limusin, Madura, Pasundan, dan PO); parity nyata lulus pada fixture dengan tensor input identik dan kelas pemenang yang sama. Lihat [`docs/model/parity.md`](docs/model/parity.md). Status ini tidak menyatakan production readiness karena rehearsal operasional dan aksesibilitas masih terpisah.

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
pnpm run backend:smoke -- --image /path/to/fixture.jpg  # Reset DB development lalu smoke Keras nyata

pnpm run mobile:build    # Build APK debug lokal (bukan artefak Play Store)
pnpm run mobile:release  # Build AAB release bertanda tangan untuk Play Store
pnpm run mobile:deploy   # Build dan install APK
pnpm run mobile:run      # Build, install, dan jalankan aplikasi
pnpm run mobile:test     # Jalankan unit test Android
pnpm run web:setup       # Install dependensi Web Admin
pnpm run web:test        # Jalankan test Web Admin
pnpm run web:check       # Periksa tipe dan komponen Svelte
pnpm run test            # Jalankan seluruh unit test
pnpm run build           # Build backend dan Web Admin
```

Backend lokal tersedia di `http://localhost:8000`; dokumentasi OpenAPI tersedia di `http://localhost:8000/docs`. `backend:smoke` bersifat destruktif terhadap data development karena menjalankan `backend:dev`; gunakan hanya untuk database SQLite development lokal.

## Konfigurasi Mobile

Salin konfigurasi lokal sebelum build:

```bash
cp apps/mobile/local.properties.example apps/mobile/local.properties
```

Atur `API_BASE_URL` di `apps/mobile/local.properties`. Berkas tersebut bersifat lokal dan tidak boleh di-commit. Konfigurasi upload key dan alur AAB Play Store dijelaskan di [`docs/mobile/README.md`](docs/mobile/README.md).

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
