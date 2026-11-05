# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Arya | Implementasi TODO(T1) untuk mendukung sintaks `INSERT INTO ... SELECT` di `crud/parser.py` | Diterima | Memanggil recursive descent `self._select()` saat mendeteksi token lookahead `SELECT` sesuai grammar SPESIFIKASI.md Bagian 3 dan konsep Bab 6 *Crafting Interpreters*. | Menjalankan `pytest tests/test_parser.py -k test_insert_select`, test berubah dari FAILED menjadi PASSED (12/12 passed). |
| 2 | Arya | Perbaikan Bug R1: urutan pencarian scope terbalik pada `_lookup()` di `crud/resolver.py` | Diterima | Menelusuri rantai scope dari `self.scope` ke `parent` (terdalam ke terluar) sesuai konsep Bab 11 *Crafting Interpreters* dan SPESIFIKASI.md 4.3. | Menulis test regresi `test_regresi_r1_shadowing_alias_subquery` di `tests/test_tambahan.py` (gagal sebelum fix, lulus setelah fix). |
| 3 | Arya | Perbaikan Bug R2: penambahan `self._pop()` pada statement `DELETE` di `crud/resolver.py` | Diterima | Memastikan siklus scope simetris dan statement berdiri sendiri tanpa kebocoran alias ke statement berikutnya sesuai SPESIFIKASI.md 4.5. | Menulis test regresi `test_regresi_r2_kebocoran_scope_statement_delete` di `tests/test_tambahan.py` (gagal sebelum fix, lulus setelah fix). |
| 4 | Arya | Implementasi TODO(T2) untuk resolusi kolom tanpa qualifier di `crud/resolver.py` | Diterima | Mengambil tabel di scope terdalam: jika tepat 1 tabel maka diisi `col.resolved`, jika > 1 tabel diberi warning "ambigu tanpa skema" dan resolved None sesuai SPESIFIKASI.md 4.3. | `pytest tests/test_resolver.py` lulus 100% (termasuk `test_kolom_tanpa_qualifier_satu_tabel`), ditambah test kasus tepi di `tests/test_tambahan.py`. |
| 5 | Arya | Perbaikan Bug A1: subquery pada statement UPDATE salah ditandai `U` alih-alih `R` di `crud/analyzer.py` | Diterima | Mengubah argumen `_collect(..., "U")` menjadi `_collect(..., "R")` pada klausa `SET` dan `WHERE` di `_update` sesuai SPESIFIKASI.md Bagian 5 (subquery selalu `R`). | Menulis test regresi `test_regresi_a1_subquery_update_selalu_read` di `tests/test_tambahan.py` (gagal sebelum fix dengan `assert {'U'} == {'R'}`, lulus setelah fix). |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
