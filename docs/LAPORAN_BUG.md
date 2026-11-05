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

**Perbaikan.** Menambahkan satu baris pemanggilan `self._pop()` di akhir metode `_delete()` pada file `crud/resolver.py`, sehingga konsisten dengan `_select()` dan `_update()`.

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
