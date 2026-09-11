---
status: proposed
---

# Sinkronkan Artikel Panduan sebagai snapshot lokal

Mobile menampilkan Artikel Panduan dari Room dan mengganti seluruh cache per locale secara atomik setelah berhasil mengambil snapshot lengkap artikel aktif; snapshot bawaan APK dipakai hanya sebelum locale pernah berhasil disinkronkan. Pendekatan ini dipilih daripada request per artikel atau cache parsial karena daftar dan detail harus konsisten saat offline, penonaktifan harus dapat menarik konten pada sync berikutnya, dan kegagalan jaringan tidak boleh merusak salinan terakhir yang valid.

## Konsekuensi

Backend harus menerbitkan snapshot lengkap dengan versi opaque, mobile harus mencatat keberhasilan sync meskipun snapshot kosong, dan pembaruan konten tidak terlihat pada perangkat yang tetap offline sampai sync berikutnya berhasil.

Migrasi dari Profil Jenis ke Artikel Panduan sengaja tidak menyediakan downgrade: penyusunan field profil lama menjadi `body` tidak dapat dibalik tanpa kehilangan struktur. Rollback melewati revisi `0009_article_cms` harus memulihkan backup database sebelum migrasi.
