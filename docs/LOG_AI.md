# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Fatur Hanafi | apakah setiap test yang ada dalam folder test itu tidak boleh diubah karena memiliki API dan perilakunya sendiri? | Diterima | Dijelaskan bahwa tes bukan API program. tes sebaiknya diperlakukan sebagai spesifikasi perilaku dan hanya diubah jika perilaku yang diharapkan memang berubah, bukan untuk menutupi bug. | Ditinjau sebagai panduan konseptual. |
| 2 | Fatur Hanafi | baris 6 kolom 41 itu apakah berarti suatu query di baris 6 di file sql laporan penjualan? lalu kolom 41 itu merujuk ke mana? | Diterima | Dijelaskan bahwa baris dan kolom merujuk pada posisi karakter di file SQL, bukan kolom tabel. Saat diperiksa, kolom 41 menunjuk karakter < pada operator <>. | Menghitung posisi karakter pada baris 6 |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
