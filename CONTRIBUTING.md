# Panduan Kontribusi SapiKenal

## Alur Kerja

1. Buat branch dari `dev` dengan nama `feat/...`, `fix/...`, `docs/...`, atau `chore/...`.
2. Buat perubahan sekecil mungkin dan gunakan istilah domain dari [`CONTEXT.md`](CONTEXT.md).
3. Jalankan test yang relevan sebelum push.
4. Buat Pull Request ke `dev` dengan ringkasan perubahan dan cara verifikasi.

Gunakan format Conventional Commits:

```text
<type>(<scope>): <deskripsi singkat>
```

Contoh:

```text
feat(model): add cattle breed classifier
fix(mobile): handle empty identification result
docs(api): document prediction endpoint
```

## Standar Kode

### Mobile (`apps/mobile`)

- Gunakan Kotlin dan Jetpack Compose.
- Jalankan pekerjaan jaringan dan inferensi di luar main thread.
- Pertahankan aksesibilitas dan dukungan minimum Android yang sudah ditetapkan proyek.

### Backend (`apps/backend`)

- Gunakan type hint Python dan skema Pydantic pada trust boundary.
- Validasi input API dan kembalikan error yang konsisten.
- Jangan menyimpan credential atau data sensitif dalam source code.

### Web (`apps/web`)

- Ikuti pola Svelte yang sudah ada.
- Jalankan pemeriksaan tipe dan test sebelum push.

## Verifikasi

Jalankan perintah yang sesuai dengan area perubahan:

```bash
pnpm run backend:test
pnpm run mobile:test
pnpm run mobile:build
pnpm run web:check
pnpm run web:test
```

## Dokumentasi dan Data

- Tempatkan dokumentasi di kategori yang sesuai di `docs/`.
- Jangan menambahkan dokumen akademik proyek lama.
- Jangan commit dataset mentah, model besar, `.env`, `local.properties`, keystore, token, atau dump database produksi.
- Catat sumber, label, lisensi, dan transformasi dataset di `docs/dataset/` ketika dataset mulai digunakan.
