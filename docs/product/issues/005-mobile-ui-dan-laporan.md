# Migrasikan pengalaman mobile dan laporan

## Tujuan

Menampilkan identifikasi jenis sapi secara konsisten pada onboarding, hasil, riwayat, laporan PDF, panduan, dan halaman tentang.

## Dependensi

- Issue 003.
- Issue 004.

## Scope

- Ganti string penyakit dalam resource Indonesia dan Inggris.
- Tampilkan satu jenis teratas dan tingkat keyakinan tanpa peringatan threshold khusus.
- Ganti pemetaan warna/ikon/label PMK, LSD, dan sehat dengan empat jenis sapi.
- Perbarui riwayat, detail hasil, ekspor/bagikan PDF, dan accessibility semantics.
- Hapus disclaimer klinis yang tidak relevan; ganti dengan batasan bahwa hasil adalah klasifikasi model dan bukan validasi objek.
- Ganti panduan penyakit menjadi profil jenis yang berfokus pada kelebihan dan kekurangan.
- Pastikan kamera/galeri tidak menjanjikan validasi bahwa objek adalah sapi.

## Kriteria penerimaan

- [ ] Alur kamera dan galeri berakhir pada salah satu dari empat jenis beserta persentase.
- [ ] Semua skor dapat ditampilkan dengan label yang benar.
- [ ] Riwayat dan PDF mempertahankan hasil, skor, mode, dan versi model.
- [ ] Tidak ada teks pengguna yang menyebut deteksi penyakit, diagnosis, PMK, LSD, sehat sebagai kelas, atau objek non-sapi sebagai penolakan model.
- [ ] Profil empat jenis dapat dibaca dalam bahasa yang didukung.
- [ ] Hasil dapat dibaca pembaca layar dan tidak bergantung pada warna saja.
- [ ] Unit/acceptance test mobile lulus.

## Verifikasi

```bash
pnpm run mobile:test
```

Lakukan pemeriksaan manual singkat pada font scale besar untuk layar hasil dan profil jenis.
