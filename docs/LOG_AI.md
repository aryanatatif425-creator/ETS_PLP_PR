# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.
Setiap baris di bawah ini merepresentasikan satu sesi interaksi dengan coding agent,
dengan fokus pada isi tugas inti dan keputusan yang diambil.

| No | Pengguna | Isi tugas inti (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
|---|---|---|---|---|---|
| 1 | Arya | Menambahkan dukungan klausa `SELECT` pada parser untuk perintah `INSERT ... SELECT` | Diterima | Saat parser mendeteksi keyword `SELECT`, dialihkan ke fungsi `_select()` yang sudah ada tanpa perlu membuat logika parsing baru. | `test_insert_select` di `tests/test_parser.py` lulus. |
| 2 | Arya | Alias subquery `x` salah ter-resolve ke tabel luar; seharusnya digunakan alias di dalam subquery. | Diterima | Mekanisme pencarian scope dibalik: mulai dari scope terdalam (`self.scope`) naik ke `parent`, sehingga alias di subquery menutupi alias luar. | `test_regresi_r1_shadowing_alias_subquery` di `tests/test_tambahan.py`; gagal sebelum perbaikan, lulus sesudahnya. |
| 3 | Arya | Alias `s` dari statement `DELETE` bocor ke statement `SELECT` berikutnya. | Diterima | Fungsi `_delete()` menambahkan panggilan `_pop()` di akhir untuk membuang scope setelah statement selesai, mencegah kebocoran alias ke statement berikutnya. | `test_regresi_r2_kebocoran_scope_statement_delete` di `tests/test_tambahan.py`; sebelumnya tidak error, sekarang muncul error alias `'s'` tidak terdefinisi. |
| 4 | Arya | Menentukan resolusi kolom tanpa qualifier (misal `SELECT status FROM a, b`). | Diterima | Jika hanya satu tabel di scope, kolom dialihkan ke tabel tersebut. Jika lebih dari satu tabel, dicatat peringatan "ambiguous tanpa skema" dan `resolved` tetap kosong. | `test_kolom_tanpa_qualifier_ambigu_dua_tabel` di `tests/test_tambahan.py` dan verifikasi `test_resolver`. |
| 5 | Arya | Subquery di klausa `UPDATE` ikut dihitung operasi `U` sementara seharusnya `R`. | Diterima | Ketika mengumpulkan penggunaan tabel di `SET` atau `WHERE` di `UPDATE`, operasi awal menggunakan `U`. Diganti menjadi `R` karena subquery hanya membaca data; target luar tetap `U`. | `test_regresi_a1_subquery_update_selalu_read` di `tests/test_tambahan.py`; sebelumnya pelanggan terbaca `U`, sekarang `R`. |
| 6 | Fatur Hanafi | Bukanya apakah test-tes di folder test tidak boleh diubah karena memiliki API dan perilakunya sendiri? | Diterima | Dijelaskan bahwa test bukan merupakan API dari program aplikasinya. Test sebaiknya diperlakukan sebagai spesifikasi perilaku dan hanya diubah jika perilaku yang diharapkan memang telah berubah, bukan sekadar untuk menutupi bug. | Dinilai sebagai panduan konseptual mengenai pola pengembangan test. |
| 7 | Fatur Hanafi | Penelusuran baris 6 kolom 41 pada file `laporan_penjualan.sql`: apakah itu posisi karakter di baris 6? dan kolom 41 merujuk ke mana? | Diterema | Baris dan kolom merujuk pada posisi karakter absolut dalam file SQL, bukan kolom tabel logique. Kolom 41 menunjuk karakter `<` pada operator `<>`. | Menghitung posisi karakter pada baris 6. |

---

**Refleksi (3–5 kalimat):**

AI paling membantu untuk menghasilkan kode boilerplate dan struktur awal dari fungsi-fungsionalitas seperti `_select()`, `_pop()`, serta mereset kode berdasarkan komentar BUG dalam sumber. AI menyesatkan ketika mengasumsikan urutan pencarian scope global (dari luar ke dalam) tanpa adanya konteks kode yang ada; kesalahan ini terdeteksi melalui pengujian regresi (`test_regresi_r1_shadowing_alias_subquery`) dan diverifikasi dengan membandingkan output sebelum dan sesudah perbaikan. Untuk mencegah hal serupa, penulis selalu melintasi output AI dengan pengetahuan spesifikasi (SPESIFIKASI.md) dan menjalankan test yang sudah ada sebelum mengesampingkan kode.