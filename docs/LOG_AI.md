# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.
Setiap baris di bawah ini merepresentasikan satu sesi interaksi dengan coding agent,
dengan fokus pada isi tugas inti dan keputusan yang diambil.

| No | Pengguna | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
|---|---|---|---|---|---|
| 1 | Arya | Cara menambahkan dukungan klausa `SELECT` pada parser untuk perintah `INSERT ... SELECT` | Diterima | Saat parser mendeteksi keyword `SELECT`, dialihkan ke fungsi `_select()` yang sudah ada tanpa perlu membuat logika parsing baru. | `test_insert_select` di `tests/test_parser.py` lulus. |
| 2 | Arya | Alias subquery `x` salah ter-resolve ke tabel luar; seharusnya digunakan alias di dalam subquery. | Diterima | Mekanisme pencarian scope dibalik: mulai dari scope terdalam (`self.scope`) naik ke `parent`, sehingga alias di subquery menutupi alias luar. | `test_regresi_r1_shadowing_alias_subquery` di `tests/test_tambahan.py`; gagal sebelum perbaikan, lulus sesudahnya. |
| 3 | Arya | Alias `s` dari statement `DELETE` bocor ke statement `SELECT` berikutnya. | Diterima | Fungsi `_delete()` menambahkan panggilan `_pop()` di akhir untuk membuang scope setelah statement selesai, mencegah kebocoran alias ke statement berikutnya. | `test_regresi_r2_kebocoran_scope_statement_delete` di `tests/test_tambahan.py`; sebelumnya tidak error, sekarang muncul error alias `'s'` tidak terdefinisi. |
| 4 | Arya | Menentukan resolusi kolom tanpa qualifier (misal `SELECT status FROM a, b`). | Diterima | Jika hanya satu tabel di scope, kolom dialihkan ke tabel tersebut. Jika lebih dari satu tabel, dicatat peringatan "ambiguous tanpa skema" dan `resolved` tetap kosong. | `test_kolom_tanpa_qualifier_ambigu_dua_tabel` di `tests/test_tambahan.py` dan verifikasi `test_resolver`. |
| 5 | Arya | Subquery di klausa `UPDATE` ikut dihitung operasi `U` sementara seharusnya `R`. | Diterima | Ketika mengumpulkan penggunaan tabel di `SET` atau `WHERE` di `UPDATE`, operasi awal menggunakan `U`. Diganti menjadi `R` karena subquery hanya membaca data; target luar tetap `U`. | `test_regresi_a1_subquery_update_selalu_read` di `tests/test_tambahan.py`; sebelumnya pelanggan terbaca `U`, sekarang `R`. |
| 6 | Fatur Hanafi |  apakah test-tes di folder test tidak boleh diubah karena memiliki API dan perilakunya sendiri? | Diterima | Dijelaskan bahwa test bukan merupakan API dari program aplikasinya. Test sebaiknya diperlakukan sebagai spesifikasi perilaku dan hanya diubah jika perilaku yang diharapkan memang telah berubah, bukan sekadar untuk menutupi bug. | Dinilai sebagai panduan konseptual mengenai pola pengembangan test. |
| 7 | Fatur Hanafi | Penelusuran baris 6 kolom 41 pada file `laporan_penjualan.sql`: apakah itu posisi karakter di baris 6? dan kolom 41 merujuk ke mana? | Diterima | Baris dan kolom merujuk pada posisi karakter absolut dalam file SQL, bukan kolom tabel logis. Kolom 41 menunjuk karakter `<` pada operator `<>`. | Menghitung posisi karakter pada baris 6. |
| 8 | Fatur Hanafi | Konfirmasi keyword huruf kecil tetap diklasifikasikan KEYWORD, bukan IDENT | Diterima | SPESIFIKASI §2.2: keyword tidak peka huruf besar/kecil dan dinormalisasi ke huruf besar. | `test_keyword_huruf_kecil_dan_campuran` lulus. |
| 9 | Fatur Hanafi | Penyebab gagalnya `test_komentar_blok` di lexer | Diterima | Komentar blok `/* ... */` belum diimplementasi (TODO T3). | `test_komentar_blok` gagal sebelum fix. |
| 10 | Fatur Hanafi | Implementasi dukungan komentar blok `/* ... */` di `lexer.py` (TODO T3) | Diubah | Lexer harus membuang token komentar dan melacak nomor baris dengan benar. | `test_komentar_blok` lulus setelah fix. |
| 11 | Fatur Hanafi | Penjelasan error `test_insert_select` (`INSERT ... SELECT belum didukung`) | Diterima | Parser belum menangani klausa `SELECT` di perintah `INSERT` (TODO T1). | `test_insert_select` lulus. |
| 12 | Fatur Hanafi | Penjelasan error `test_kolom_tanpa_qualifier_satu_tabel` (`resolved` kosong) | Diterima | Resolver belum menangani kolom tanpa qualifier (TODO T2). | `test_kolom_tanpa_qualifier_satu_tabel` lulus. |
| 13 | Fatur Hanafi | Implementasi perbaikan operator `<>` (maximal munch) | Diubah | Lexer memecah `<>` menjadi dua token terpisah `<` dan `>`. | `test_regresi_operator_tidak_sama_dengan` lulus. |
| 14 | Fatur Hanafi | Implementasi perbaikan escaped quotes (`''`) pada string literal | Diubah | Lexer berhenti prematur pada tanda kutip pertama. | `test_regresi_string_escaped_quote` lulus. |
| 15 | Fatur Hanafi | Implementasi perbaikan presedensi `AND`/`OR` di parser | Diubah | Fungsi `_logical` datar memparsing `AND` dan `OR` pada level yang sama. | `test_regresi_presedensi_and_or` lulus. |
| 16 | Fatur Hanafi | Implementasi perbaikan `LEFT OUTER JOIN` (keyword `OUTER` opsional) | Diubah | Parser menolak token `OUTER` karena tidak dikonsumsi. | `test_regresi_left_outer_join` lulus. |
| 17 | Fatur Hanafi | Implementasi perbaikan panic mode recovery (berhenti di `;`) | Diubah | Parser membuang sisa file sampai EOF. | `test_regresi_panic_mode_recovery` lulus. |
| 18 | Fatur Hanafi | Lengkapi isi `LAPORAN_BUG.md` untuk setiap bug | Diubah | Dokumen laporan bug belum terisi entri resmi. | `docs/LAPORAN_BUG.md` berisi entri per bug. |
| 19 | Fatur Hanafi | Isi bagian "Perbaikan" di `LAPORAN_BUG.md` sesuai bug yang diperbaiki | Diubah | Bagian perbaikan belum diisi. | `docs/LAPORAN_BUG.md` lengkap. |
| 20 | Fatur Hanafi | Verifikasi keakuratan dan kelengkapan `ground_truth.csv` | Diterima | Label dicek manual berdasarkan spesifikasi. | `ground_truth.csv` cocok SPESIFIKASI . |
| 21 | Fatur Hanafi | Buat test regresi + test kasus tepi (termasuk TODO T3) di `test_tambahan.py` | Diubah | Test tambahan belum lengkap. | 16 test lulus di `tests/test_tambahan.py`. |

---

**Refleksi (3–5 kalimat):**

AI paling membantu untuk menghasilkan kode boilerplate dan struktur awal dari fungsi-fungsionalitas seperti `_select()`, `_pop()`, serta mereset kode berdasarkan komentar BUG dalam sumber. AI menyesatkan ketika mengasumsikan urutan pencarian scope global (dari luar ke dalam) tanpa adanya konteks kode yang ada; kesalahan ini terdeteksi melalui pengujian regresi (`test_regresi_r1_shadowing_alias_subquery`) dan diverifikasi dengan membandingkan output sebelum dan sesudah perbaikan. Untuk mencegah hal serupa, penulis selalu melintasi output AI dengan pengetahuan spesifikasi (SPESIFIKASI.md) dan menjalankan test yang sudah ada sebelum mengesampingkan kode.