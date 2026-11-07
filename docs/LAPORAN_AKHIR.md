# Laporan Akhir

## 1. Hasil evaluasi

```text
$ .venv/bin/python evaluate.py

Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')

```

## 2. Tiga kasus di mana regex salah

### Kasus 1: DELETE ditandai sebagai Read (R) bukan Delete (D)
- **SQL**: `DELETE FROM keranjang WHERE dibuat < :batas;` (baris 8, `campuran_error.sql`)
- **Kesalahan regex**: Regex mencatat `keranjang` sebagai `R` karena hanya mencocokkan kata kunci tabel secara leksikal tanpa memahami konteks sintaktis pernyataan `DELETE`.
- **Mengapa parser benar**: Parser menggunakan *recursive descent parsing* yang mengenali struktur pernyataan `DELETE` sebagai satu kesatuan sintaks (*Crafting Interpreters* Bab 6: Parsing Statements), sehingga menetapkan operasi `D` pada tabel target. Ini membedakan peran tabel berdasarkan gramatika pernyataan, bukan sekadar menemukan nama tabel.

### Kasus 2: Baris sintaks rusak masih dihitung sebagai operasi valid
- **SQL**: `SELECT id nama, FROM pesanan;` (baris 4, `campuran_error.sql`)
- **Kesalahan regex**: Regex tetap mengekstrak `pesanan` sebagai `R` meskipun baris tersebut memuat kesalahan sintaks koma menggantung (`trailing comma`).
- **Mengapa parser benar**: Parser memvalidasi struktur gramatika terlebih dahulu. Ketika terjadi kesalahan sintaks, parser mencatat diagnostik error dan melakukan pemulihan kesalahan (*panic mode error recovery*, Bab 6) hingga batas titik koma (`;`). Baris yang rusak tidak dimasukkan ke dalam AST, sehingga tidak menghasilkan entri CRUD palsu (*false positive*).

### Kasus 3: Tabel dalam comma-separated FROM terlewat oleh regex
- **SQL**: `SELECT p.id, p.nama FROM pelanggan p, pesanan o WHERE o.pelanggan_id = p.id ...` (baris 2, `audit.sql`)
- **Kesalahan regex**: Regex melewatkan tabel `pesanan` sebagai `R` (*false negative*) karena pola pencocokan regex gagal menangani multi-tabel dengan pemisah koma dan alias berturut-turut.
- **Mengapa parser benar**: Parser membangun pohon sintaks (AST) yang secara terstruktur merekam setiap `TableRef` di dalam daftar tabel klausa `FROM` (`_from_clause()`), termasuk resolusi alias dan relasi join, sehingga seluruh tabel sumber terdeteksi secara deterministik.

## 3. Batas pendekatan kami

1. **CTE (`WITH` clause) tidak didukung**
   - **Contoh SQL**: `WITH cte AS (SELECT id FROM pesanan) SELECT * FROM cte;`
   - **Akibat**: Tabel `cte` tidak teridentifikasi karena tata bahasa (*grammar*) belum mengenal produksi klausa `WITH`, sehingga matriks menjadi kosong atau tidak lengkap.
   - **Informasi yang dibutuhkan**: Perluasan aturan grammar BNF untuk mengenali `with_clause` serta penambahan tabel simbol sementara untuk memetakan alias CTE ke subquery definisinya.

2. **Query dinamis / string concatenation**
   - **Contoh SQL**: Query yang disusun secara dinamis di tingkat aplikasi menggunakan konkatenasi string atau dieksekusi via `EXECUTE format(...)`.
   - **Akibat**: Tabel dan operasi tidak dapat dideteksi secara statis (*static analysis*) karena teks SQL lengkap baru terbentuk saat *runtime*.
   - **Informasi yang dibutuhkan**: Analisis jejak runtime (*query logging / execution tracing*) atau evaluasi ekspresi simbolik parsial.

3. **Tidak ada katalog skema database untuk resolusi nama ambigu**
   - **Contoh SQL**: `SELECT nama FROM pelanggan, pesanan;` tanpa qualifier di mana kolom `nama` ada di kedua tabel.
   - **Akibat**: Sistem hanya mencatat peringatan *"ambigu tanpa skema"* dan atribut `resolved` dibiarkan kosong sesuai SPESIFIKASI §4.3.
   - **Informasi yang dibutuhkan**: Akses ke *database catalog / schema dictionary* (metadata kolom untuk setiap tabel) untuk menentukan relasi kepemilikan kolom secara akurat.

## 4. Pembagian kerja

| No | Nama | Todo | Bug | Dokumen | tests | data |
|---|---|---|---|---|---|---|
| 1 | Arya | T1, T2 | R1, R2, A1 | KARTU_DESAIN, LOG_AI, LAPORAN_BUG, LAPORAN_AKHIR | test_tambahan.py | |
| 2 | Fatur | T3 | L1, L2, L3, P1, P2, P3 | LOG_AI, LAPORAN_BUG, LAPORAN_AKHIR | test_tambahan.py | ground_truth.csv |

### Cara Memastikan Pemahaman Seluruh Kode

Untuk memastikan kedua anggota menguasai arsitektur sistem secara menyeluruh dan siap menghadapi evaluasi lisan individual:
1. **Peer Code Review & Walkthrough**: Setiap commit dan perubahan pada pipeline diuji dan dibedah bersama melalui sesi diskusi, di mana penulis menjelaskan alasan teknis pemilihan algoritma dan kaitannya dengan bab pada *Crafting Interpreters*.
2. **Cross-Validation Test Regresi**: Pembuatan 16 test di `tests/test_tambahan.py` divalidasi silang untuk membuktikan bahwa Arya memahami penanganan di level *lexer/parser* dan Fatur memahami penanganan di level *resolver/analyzer*.
3. **Penyusunan Dokumen Bersama**: Penulisan akar masalah pada `LAPORAN_BUG.md` dan 5 kartu keputusan pada `KARTU_DESAIN.md` didiskusikan secara mendalam agar keduanya memahami alternatif yang ditolak dan justifikasi teoritisnya.
