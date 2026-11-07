# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: Urutan Pencarian Rantai Scope Terbalik pada Resolver (Broken Shadowing)

**Ditemukan oleh:** Arya · **Diperbaiki oleh:** Arya

**Gejala.** Pada query dengan subquery di mana alias di query luar sama dengan alias di dalam subquery (misal `x`), kolom yang dirujuk di dalam subquery (`x.pelanggan_id`) salah dihubungkan ke tabel di query luar (`pelanggan`), bukan tabel lokal subquery (`pesanan`). Menurut SPESIFIKASI.md Bagian 4.3: *"qualifier dicari mulai dari scope terdalam ke luar. Yang pertama ditemukan dipakai. Akibatnya alias di subquery menutupi alias yang sama di luar (shadowing)"*.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x);
```

**Akar masalah.** *Crafting Interpreters* Bab 11 (Resolving and Binding) menjelaskan konsep *lexical scoping* dan *environment chaining*. Resolusi variabel/identifier harus dimulai dari lingkup lokal terdalam (*innermost scope*) lalu bergerak keluar (*parent/enclosing scope*). Kode lama di `crud/resolver.py` mengumpulkan scope dari terdalam ke terluar di list `chain`, namun mengiterasinya dengan `for scope in reversed(chain):`. Pemanggilan `reversed()` ini membalik urutan pencarian menjadi dari terluar ke terdalam, sehingga alias pada query luar mendahului dan menimpa alias di dalam subquery.

**Perbaikan.** Pada file `crud/resolver.py`, fungsi `_lookup()` diubah untuk menelusuri rantai scope langsung dari `self.scope` ke `scope.parent` menggunakan loop `while scope is not None:`. Pendekatan alternatif adalah tetap menggunakan list `chain` tanpa memanggil `reversed()`, namun penelusuran rantai pointer `parent` langsung lebih bersih, tidak mengalokasikan list sementara, dan secara langsung mencerminkan struktur *environment walk* di Bab 11.

**Test regresi.** `test_regresi_r1_shadowing_alias_subquery` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu mengidentifikasi anomali resolusi alias `x` saat visualisasi AST pada `data/sample/audit.sql`. Kami memverifikasinya secara independen dengan menulis test regresi di `tests/test_tambahan.py` yang memicu assertion error (`'pelanggan' == 'pesanan'`) pada kode lama dan lulus setelah perbaikan.

---

## Bug 2: Kebocoran Scope pada Statement DELETE Akibat Ketiadaan `_pop()`

**Ditemukan oleh:** Arya · **Diperbaiki oleh:** Arya

**Gejala.** Pada berkas SQL multi-statement, alias tabel yang dideklarasikan pada statement `DELETE` (misal `s` pada `DELETE FROM sesi s`) bocor dan tetap dapat diakses oleh statement berikutnya. Contohnya pada `SELECT s.id FROM pengguna u`, rujukan `s.id` salah di-resolve ke tabel `sesi` dari statement `DELETE` sebelumnya tanpa menghasilkan error. Menurut SPESIFIKASI.md Bagian 4.5: *"Setiap statement berdiri sendiri: Setelah satu statement selesai di-resolve, tidak boleh ada scope tersisa. Alias dari statement sebelumnya tidak boleh terlihat oleh statement berikutnya."* dan Bagian 4.3 mewajibkan pelaporan error `alias 's' tidak terdefinisi`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
DELETE FROM sesi s WHERE s.kedaluwarsa < :sekarang;
SELECT s.id FROM pengguna u WHERE u.aktif = 1;
```

**Akar masalah.** *Crafting Interpreters* Bab 11 (Resolving and Binding) menjelaskan siklus hidup lingkup/lingkungan simetris (*symmetric scope lifecycle*): setiap blok atau statement yang membuka scope baru melalui `_push()` wajib menutup scope tersebut dengan `_pop()` saat penyusuran node selesai agar stack kembali ke status bersih. Pada `crud/resolver.py`, fungsi `_delete()` memanggil `self._push()`, namun lupa memanggil `self._pop()`. Scope `DELETE` menjadi residu (*scope leakage*) yang tertinggal dan salah menjadi scope induk bagi statement berikutnya.

**Perbaikan.** Menambahkan satu baris pemanggilan `self._pop()` di akhir metode `_delete()` pada file `crud/resolver.py`, sehingga konsisten dengan `_select()` dan `_update()`. Alternatif membuang seluruh stack scope setiap pergantian statement tidak dipilih karena metode `_pop()` simetris lebih elegan dan mematuhi kaidah struktur compiler yang bersih.

**Test regresi.** `test_regresi_r2_kebocoran_scope_statement_delete` di `tests/test_tambahan.py`.

**Peran AI.** AI menemukan kejanggalan pada keluaran `--ast` berkas `data/sample/audit.sql` baris 18 di mana alias `s` terhubung ke `sesi`. Kami memverifikasinya dengan meninjau implementasi `_delete()` di `crud/resolver.py` dan membuat test regresi yang membuktikan kegagalan deteksi error sebelum kode diperbaiki.

---

## Bug 3: Subquery pada Statement UPDATE Salah Ditandai Operasi U Alih-Alih R

**Ditemukan oleh:** Arya · **Diperbaiki oleh:** Arya

**Gejala.** Pada statement `UPDATE` yang mengandung subquery di klausa `SET` maupun `WHERE`, tabel sumber di dalam subquery salah ditandai melakukan operasi `U` (Update) alih-alih `R` (Read). Contohnya pada `UPDATE pesanan SET status = 'BATAL' WHERE pelanggan_id IN (SELECT id FROM pelanggan WHERE diblokir = 1)`, tabel `pelanggan` menghasilkan set operasi `{'U'}`, padahal menurut SPESIFIKASI.md Bagian 5: *"UPDATE: Tabel target: U, Tabel lain (subquery di SET maupun WHERE): R. Membaca tabel lewat subquery selalu R, apa pun jenis statement luarnya."*

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
UPDATE pesanan SET status = 'BATAL' WHERE pelanggan_id IN (SELECT id FROM pelanggan WHERE diblokir = 1);
```

**Akar masalah.** *Crafting Interpreters* Bab 5 (Representing Code / Syntax Trees) menjelaskan bahwa evaluasi dan pemaknaan node AST bergantung pada konteks operasi dalam pohon (*tree walk*). Pada `crud/analyzer.py`, saat mengevaluasi `ast.Update`, fungsi memanggil `_collect(assignment.value, usage, "U")` dan `_collect(stmt.where, usage, "U")`. Karena parameter operasi yang diteruskan adalah `"U"`, saat penelusuran rekursif menemukan node subquery (`ast.Subquery`, `ast.Exists`, `ast.InExpr`), pemanggilan `_collect_select(expr.query, usage, op)` tetap membawa operasi `"U"`. Akibatnya seluruh tabel di dalam subquery salah dicatat sebagai `U`.

**Perbaikan.** Pada file `crud/analyzer.py`, argumen pemanggilan `_collect` di dalam cabang `isinstance(stmt, ast.Update)` diubah dari `"U"` menjadi `"R"`, konsisten dengan penanganan `_collect(stmt.where, usage, "R")` pada statement `ast.Delete`.

**Test regresi.** `test_regresi_a1_subquery_update_selalu_read` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu meninjau kesesuaian antara tabel aturan CRUD di `SPESIFIKASI.md` Bagian 5 dengan penelusuran AST di `crud/analyzer.py`. Kami memverifikasinya dengan menyusun test regresi yang membuktikan assertion failure (`assert {'U'} == {'R'}`) sebelum perbaikan dan lolos sesudahnya.

---

## Bug 4: Keyword Huruf Kecil Dianggap Identifier

**Ditemukan oleh:** Fatur · **Diperbaiki oleh:** Fatur

**Gejala.** Input query yang memuat kata kunci berhuruf kecil atau kombinasi (misalnya `select id from t`) menghasilkan token `IDENT` alih-alih `KEYWORD`:
```text
Token(IDENT, 'select', 1:1)
```
Hal ini menyebabkan pengujian `tests/test_lexer.py::test_keyword_huruf_kecil` gagal. Menurut **SPESIFIKASI.md Bagian 2.2**, kata kunci SQL bersifat *case-insensitive* (tidak peka huruf besar/kecil): `select`, `Select`, dan `SELECT` harus diklasifikasikan sebagai token `KEYWORD`, serta nilai tokennya wajib dinormalisasi ke huruf besar (`"SELECT"`).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
select id from t;
```

**Akar masalah.** Pelanggaran penanganan kata kunci leksikal (*Reserved Words vs. Identifiers*, *Crafting Interpreters* Bab 4: Scanning). Pada fungsi `_word()` di `crud/lexer.py:176-183`, scanner mengambil potongan teks kata dan mencocokkannya secara langsung dengan ekspresi `if text in KEYWORDS:`. Karena himpunan `KEYWORDS` menyimpan kata kunci dalam bentuk huruf kapital penuh (`"SELECT"`, `"FROM"`), pengecekan keanggotaan bawaan Python yang *case-sensitive* bernilai `False` ketika menerima `"select"`. Scanner kemudian keliru mengarahkan kata tersebut ke blok `else` dan membentuk token `TokenType.IDENT`.

**Perbaikan.** Pada `crud/lexer.py` di fungsi `_word()`, teks yang dipindai dikonversi ke huruf besar (`upper = text.upper()`) sebelum diperiksa keanggotaannya di `KEYWORDS`. Jika cocok, token disimpan sebagai `KEYWORD` dengan nilai `upper` (ternormalisasi); jika tidak, tetap disimpan sebagai `IDENT` dengan teks aslinya. Alternatif menambahkan variasi huruf kecil ke himpunan `KEYWORDS` tidak dipilih karena tidak menangani huruf campuran (seperti `sElEcT`) dan nilai token tetap harus dinormalisasi ke huruf besar.

**Test regresi.** `test_regresi_keyword_huruf_kecil_dan_campuran` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu menganalisis penyebab kegagalan assert pada `test_lexer.py` dan menyarankan normalisasi nilai token ke huruf besar sesuai spesifikasi. Verifikasi dilakukan secara mandiri dengan mengeksekusi `pytest tests/test_lexer.py`.

---

## Bug 5: Operator <> Tidak Dikenali (Maximal Munch)

**Ditemukan oleh:** Fatur · **Diperbaiki oleh:** Fatur

**Gejala.** Saat memproses query dengan operator perbandingan tidak sama dengan (`<>`), seperti pada `laporan_penjualan.sql` baris 6 (`o.catatan <> 'FROM rahasia'`), parser melempar error:
```text
ParseError: Baris 6, kolom 41: diharapkan ekspresi, ditemukan '>'
```
Error ini menyebabkan file `laporan_penjualan.sql` gagal diproses dan seluruh matriks CRUD-nya kosong. Menurut **SPESIFIKASI.md Bagian 2.5**, operator `<>` adalah satu token `OP` utuh, bukan dua token terpisah `<` lalu `>`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT 1 FROM t WHERE a <> 1;
```

**Akar masalah.** Pelanggaran prinsip *Maximal Munch* / *Longest Match* (*Crafting Interpreters* Bab 4: Scanning). Prinsip ini menyatakan bahwa scanner wajib mengonsumsi karakter sebanyak mungkin untuk menghasilkan token terpanjang yang valid. Pada fungsi `_scan_token()` di `crud/lexer.py:118-121`, saat menemukan karakter `<`, scanner hanya memeriksa apakah karakter berikutnya adalah `=` (`<=`). Scanner mengabaikan kemungkinan karakter `>`, sehingga karakter `<` langsung dijadikan token `TokenType.OP`, dan karakter `>` pada pemindaian berikutnya menjadi token operator terpisah yang berdiri sendiri. Parser yang menerima dua operator berurutan (`<` diikuti `>`) gagal mem-parse ekspresi.

**Perbaikan.** Pada `crud/lexer.py` di fungsi `_scan_token()`, ditambahkan cabang pengecekan lookahead `elif self._match(">"): op = "<>"` saat menemukan karakter `<`. Hal ini memastikan operator `<>` langsung dikonsumsi sebagai satu token `OP` utuh sesuai prinsip *Maximal Munch*. Alternatif menggabungkan token `<` dan `>` di tingkat parser tidak dipilih karena `<>` secara leksikal adalah satu kesatuan operator SQL dan memperbaikinya di parser melanggar pemisahan fase leksikal/sintaksis.

**Test regresi.** `test_regresi_operator_tidak_sama_dengan` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu melacak bahwa pesan error di kolom 41 menunjuk tepat ke karakter `>`, mengonfirmasi token terbelah. Verifikasi dilakukan dengan menguji pemanggilan `tokenize("a <> b")`.

---

## Bug 6: Karakter Kutip Lolos (Escaped Quotes) pada String Literal

**Ditemukan oleh:** Fatur · **Diperbaiki oleh:** Fatur

**Gejala.** Query yang mengandung tanda kutip ganda berturut-turut di dalam string literal (seperti `c.nama = 'O''Brien'` pada `pemeliharaan.sql` baris 6 dan `'O''Neil'` pada baris 9) memicu syntax error karena string terputus prematur: token string hanya bernilai `'O'`, sedangkan sisa teks `Brien'` menyebabkan parser crash. Menurut **SPESIFIKASI.md Bagian 2.4**, dua kutip berturut-turut di dalam string (`''`) mewakili satu karakter kutip, sehingga `'O''Brien'` harus menjadi satu token `STRING` bernilai `O'Brien`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT 'O''Brien' FROM t;
```

**Akar masalah.** Penanganan karakter lolos pada string literal (*Escaped Characters / String Literals*, *Crafting Interpreters* Bab 4: Scanning). Pada fungsi `_string()` di `crud/lexer.py:155-163`, perulangan pemindaian karakter string langsung melakukan `break` segera setelah menemukan karakter kutip `'` (`if ch == "'": break`). Scanner tidak melakukan *lookahead* untuk memeriksa apakah tanda kutip tersebut diikuti oleh tanda kutip tunggal kedua (`''`).

**Perbaikan.** Pada `crud/lexer.py` di fungsi `_string()`, saat menemukan karakter kutip `'`, ditambahkan pengecekan `if self._match("'"): chars.append("'")`. Jika kutip diikuti kutip kedua (`''`), scanner mengonsumsinya sebagai satu karakter kutip di dalam string; jika tidak, perulangan berhenti (`break`) sebagai penutup string. Alternatif menggunakan `replace("''", "'")` pasca-pembacaan tidak dipilih karena menyulitkan penentuan batas akhir string yang valid secara deterministik.

**Test regresi.** `test_regresi_string_escaped_quote` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu merumuskan penanganan `self._match("'")` yang rapi di dalam loop `_string()`. Diverifikasi dengan memastikan `tokenize("'O''Brien'")[0].value == "O'Brien"`.

---

## Bug 7: Presedensi Logika AND dan OR Disamakan

**Ditemukan oleh:** Fatur · **Diperbaiki oleh:** Fatur

**Gejala.** Ekspresi logika yang menggabungkan operator `AND` dan `OR` tanpa tanda kurung (seperti pada klausa WHERE di `audit.sql` baris 4–6 dan `pemeliharaan.sql` baris 6) diparsing secara datar dari kiri ke kanan. Pohon AST yang terbentuk menempatkan `AND` di tingkat teratas (root), sehingga ekspresi `a OR b AND c` keliru diartikan menjadi `(a OR b) AND c`. Menurut **SPESIFIKASI.md Bagian 3.1**, operator `AND` (Tingkat 2) memiliki presedensi lebih tinggi daripada `OR` (Tingkat 1), sehingga `a OR b AND c` wajib diparsing menjadi `a OR (b AND c)`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT 1 FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** Pelanggaran penjenjangan presedensi ekspresi (*Stratified Grammar for Precedence*, *Crafting Interpreters* Bab 6: Parsing Expressions). Pada fungsi `_logical()` di `crud/parser.py:252-258`, operator `AND` dan `OR` dievaluasi di dalam perulangan `while self._check_kw("AND", "OR"):` yang sama. Kode ini memperlakukan `AND` dan `OR` pada tingkat hierarki grammar yang setara dengan sifat asosiatif kiri, bertentangan dengan aturan tata bahasa formal SQL.

**Perbaikan.** Pada `crud/parser.py`, fungsi `_logical()` dipecah menjadi dua fungsi berjenjang: `_or()` (Tingkat 1) dan `_and()` (Tingkat 2), dengan `_expr()` memanggil `_or()`. Karena `_or()` memanggil `_and()` sebagai operannya, operator `AND` terikat lebih erat di dalam pohon AST dibandingkan `OR`. Alternatif menggunakan algoritma *Pratt Parsing* atau restrukturisasi AST pasca-parse tidak dipilih karena pemisahan fungsi berjenjang pada *recursive descent parser* jauh lebih sederhana dan langsung mencerminkan aturan gramatika formal.

**Test regresi.** `test_regresi_presedensi_and_or` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu memvalidasi anomali pohon AST pada `audit.sql` baris 2 melalui opsi `--ast`. Verifikasi dilakukan dengan memeriksa hierarki node `BinaryOp` hasil parse ekspresi campuran.

---

## Bug 8: Parsing LEFT OUTER JOIN Menolak Keyword Opsional OUTER

**Ditemukan oleh:** Fatur · **Diperbaiki oleh:** Fatur

**Gejala.** Query yang menggunakan sintaks eksplisit `LEFT OUTER JOIN` (seperti pada `pemeliharaan.sql` baris 5: `left outer join crm.alamat a on ...`) melempar syntax error:
```text
ParseError: Baris 5, kolom ...: diharapkan JOIN, ditemukan 'OUTER'
```
Menurut **SPESIFIKASI.md Bagian 3 (Grammar)**, aturan produksi JOIN adalah:
`join = [ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN" table_ref "ON" expr ;`
di mana keyword `OUTER` bersifat opsional setelah `LEFT`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT * FROM a LEFT OUTER JOIN b ON b.id = a.id;
```

**Akar masalah.** Ketidaksesuaian implementasi fungsi parser terhadap aturan produksi grammar (*Parsing Statements & Grammar Production*, *Crafting Interpreters* Bab 6). Pada fungsi `_join()` di `crud/parser.py:175-186`, ketika keyword `LEFT` ditemukan, parser langsung mengeksekusi `self._expect_kw("JOIN")`. Parser tidak memiliki langkah untuk mengonsumsi keyword opsional `OUTER`, sehingga token `OUTER` dianggap sebagai token ilegal yang menghentikan parsing.

**Perbaikan.** Pada `crud/parser.py` di fungsi `_join()`, ditambahkan `self._match_kw("OUTER")` tepat setelah klausa `elif self._match_kw("LEFT"):` agar keyword opsional `OUTER` dikonsumsi secara aman sebelum memeriksa keyword wajib `JOIN`. Alternatif membolehkan `OUTER` secara bebas pada `_expect_kw()` tidak dipilih karena membuat grammar terlalu longgar dan dapat meloloskan sintaks ilegal seperti `INNER OUTER JOIN`. Alternatif menyimpan jenis `"LEFT OUTER"` pada AST juga dihindari demi kompatibilitas analisis downstream.

**Test regresi.** `test_regresi_left_outer_join` di `tests/test_tambahan.py`.

**Peran AI.** AI mencocokkan grammar BNF di `SPESIFIKASI.md` dengan alur token pada `crud/parser.py`. Verifikasi dilakukan dengan mem-parse statement JOIN yang memuat keyword `OUTER`.

---

## Bug 9: Panic Mode Recovery Membuang Sisa File Sampai EOF

**Ditemukan oleh:** Fatur · **Diperbaiki oleh:** Fatur

**Gejala.** Ketika sebuah file memuat statement yang salah sintaks di baris awal atau tengah (seperti baris 4 pada `campuran_error.sql`: `SELECT id nama, FROM pesanan;`), parser langsung mengabaikan seluruh sisa statement setelahnya. Statement valid pada baris 6 (`UPDATE produk...`) dan baris 8 (`DELETE FROM keranjang...`) tidak pernah diproses dan hilang dari `crud_matrix.csv` serta `detail.csv`. Menurut **SPESIFIKASI.md Bagian 6**, pemulihan *panic mode* wajib membuang token hanya sampai dan termasuk titik koma (`;`) berikutnya, lalu melanjutkan pemrosesan statement valid setelahnya.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT id, FROM tabel_rusak;
SELECT id FROM tabel_valid;
```

**Akar masalah.** Implementasi pemulihan kesalahan yang keliru (*Error Recovery & Panic Mode*, *Crafting Interpreters* Bab 6). Fungsi `_synchronize()` pada `crud/parser.py:90-95` berisi loop:
```python
while not self._at_end():
    self._advance()
```
Loop ini membuang semua token tanpa henti hingga mencapai `EOF`. Parser gagal melakukan sinkronisasi pada batas statement (tanda titik koma `;`), sehingga satu kesalahan sintaks merusak pemrosesan seluruh berkas.

**Perbaikan.** Pada `crud/parser.py` di fungsi `_synchronize()`, loop pengabaian token diubah menjadi `while not self._at_end(): if self._advance().type == T.SEMICOLON: return`. Pembuangan token kini berhenti tepat setelah titik koma (`;`), membatasi pemulihan pada batas statement yang rusak sehingga parser dapat memproses statement berikutnya secara normal. Alternatif sinkronisasi berbasis keyword awal statement (`SELECT`, `UPDATE`, dll.) tidak dipilih karena keyword tersebut rentan muncul di dalam subquery statement yang rusak.

**Test regresi.** `test_regresi_panic_mode_recovery` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu mengidentifikasi akar penyebab hilangnya baris 6 dan 8 pada `campuran_error.sql`. Verifikasi dilakukan dengan menjalankan parsing terhadap script multi-statement yang diselingi syntax error.

---
