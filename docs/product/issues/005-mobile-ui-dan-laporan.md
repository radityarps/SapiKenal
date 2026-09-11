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

- [x] Alur kamera dan galeri berakhir pada salah satu dari empat jenis beserta persentase.
- [x] Semua skor dapat ditampilkan dengan label yang benar.
- [x] Riwayat dan PDF mempertahankan hasil, skor, mode, dan versi model.
- [x] Tidak ada teks pengguna yang menyebut deteksi penyakit, diagnosis, PMK, LSD, sehat sebagai kelas, atau objek non-sapi sebagai penolakan model.
- [x] Profil empat jenis dapat dibaca dalam bahasa yang didukung.
- [ ] Hasil dapat dibaca pembaca layar dan tidak bergantung pada warna saja (implementasi tersedia; verifikasi TalkBack manual masih pending).
- [x] Unit/acceptance test mobile lulus (otomatis).

Status implementasi: selesai untuk kode, resource, test, dan laporan. Verifikasi manual perangkat masih tertunda; status ini tidak menyatakan camera/gallery flow, skala font besar, TalkBack, atau visual PDF telah tervalidasi.

## Verifikasi

```bash
pnpm run mobile:test
pnpm run mobile:build
```

Verifikasi manual yang masih pending: camera/gallery pada perangkat, gallery saat izin kamera ditolak, skala font besar pada hasil dan profil jenis, TalkBack, serta pemeriksaan visual PDF pada perangkat/emulator. Tandai kriteria aksesibilitas manual setelah pemeriksaan tersebut benar-benar dilakukan.
