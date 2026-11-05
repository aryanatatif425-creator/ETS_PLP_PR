# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Arya | Bagaimana cara nambahin dukungan INSERT INTO ... SELECT di parser? | Diterima | Setelah ketemu keyword SELECT, parser diarahkan ke fungsi _select() yang sudah ada, jadi tidak perlu bikin logika parsing baru. | Jalankan test_insert_select di tests/test_parser.py. |
| 2 | Arya | Kenapa alias x di subquery malah kebaca sebagai tabel luar? harusnya yang di dalam yang dipakai. | Diterima | Pencarian scope ternyata dibalik, dari luar ke dalam. Diubah jadi mulai dari scope sekarang lalu naik ke parent, jadi alias di subquery menutupi alias luar. | Jalankan test_regresi_r1_shadowing_alias_subquery di tests/test_tambahan.py; gagal sebelum fix, lulus sesudahnya. |
| 3 | Arya | Setelah statement DELETE, mengapa alias s masih terbaca di SELECT berikutnya? | Diterima | Scope DELETE dibuka tapi tidak ditutup. Ditambah _pop() agar tiap statement bersih dan tidak bocor ke statement berikutnya. | Jalankan test_regresi_r2_kebocoran_scope_statement_delete di tests/test_tambahan.py; sebelumnya tidak error, sekarang muncul error alias 's' tidak terdefinisi. |
| 4 | Arya | Kolom tanpa alias, misal SELECT status FROM a, b, seharusnya dianggap apa? | Diterima | Kalau cuma satu tabel di scope, kolom langsung diarahkan ke tabel itu. Kalau lebih dari satu, dikasih warning ambigu dan resolved dibiarkan kosong. | Jalankan test_kolom_tanpa_qualifier_ambigu_dua_tabel di tests/test_tambahan.py dan test_resolver. |
| 5 | Arya | Kenapa subquery di UPDATE ikut kehitung U? padahal cuma dibaca. | Diterima | Saat mengumpulkan tabel di SET dan WHERE masih pakai operasi U. Diganti jadi R karena subquery cuma membaca: target U, sumber R. | Jalankan test_regresi_a1_subquery_update_selalu_read di tests/test_tambahan.py; sebelumnya pelanggan kebaca U, sekarang R. |
| 6 | Fatur Hanafi | apakah setiap test yang ada dalam folder test itu tidak boleh diubah karena memiliki API dan perilakunya sendiri? | Diterima | Dijelaskan bahwa tes bukan API program. tes sebaiknya diperlakukan sebagai spesifikasi perilaku dan hanya diubah jika perilaku yang diharapkan memang berubah, bukan untuk menutupi bug. | Ditinjau sebagai panduan konseptual. |
| 7 | Fatur Hanafi | baris 6 kolom 41 itu apakah berarti suatu query di baris 6 di file sql laporan penjualan? lalu kolom 41 itu merujuk ke mana? | Diterima | Dijelaskan bahwa baris dan kolom merujuk pada posisi karakter di file SQL, bukan kolom tabel. Saat diperiksa, kolom 41 menunjuk karakter < pada operator <>. | Menghitung posisi karakter pada baris 6 |


**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
