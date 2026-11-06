# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

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

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

2. Tiga kasus di mana regex salah
Kasus 1: DELETE ditandai sebagai Read (R) bukan Delete (D)
- SQL: DELETE FROM keranjang WHERE dibuat < :batas; (baris 8, campuran_error.sql)
- Kesalahan regex: Regex mencatat keranjang sebagai R karena hanya mencari nama tabel tanpa memahami konteks pernyataan DELETE.
- Mengapa parser benar: Parser menggunakan recursive descent parsing yang mengenali struktur pernyataan DELETE sebagai satu kesatuan sintaktis, sehingga menetapkan operasi D pada tabel target (bab 6: parsing expressions & statements). Ini membedakan peran tabel dalam konteks pernyataan, bukan sekadar mencari nama tabel.
Kasus 2: Baris sintaks rusak masih dihitung sebagai operasi valid
- SQL: SELECT id nama, FROM pesanan; (baris 4, campuran_error.sql)
- Kesalahan regex: Regex mengekstrak pesanan sebagai R meskipun baris tersebut gagal diparsing (sintaks rusak).
- Mengapa parser benar: Parser memvalidasi sintaks terlebih dahulu melalui recursive descent; baris rusak diabaikan melalui panic mode recovery sehingga tidak dihitung sebagai operasi CRUD valid (bab 6: panic mode error recovery).
Kasus 3: Tabel dalam comma-separated FROM terlewat oleh regex
- SQL: SELECT p.id, p.nama FROM pelanggan p, pesanan o WHERE o.pelanggan_id = p.id ... (baris 2, audit.sql)
- Kesalahan regex: Regex tidak menemukan pesanan sebagai R (false negative) karena kesulitan menangani alias dan pemisah koma pada daftar tabel.
- Mengapa parser benar: Parser membangun pohon sintaks (AST) yang secara eksplisit merekam setiap TableRef dalam klausa FROM, termasuk alias dan pemisah koma, sehingga semua tabel terdeteksi dengan benar.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1. **CTE (`WITH` clause) tidak didukung**
   - Contoh SQL: `WITH cte AS (SELECT id FROM pesanan) SELECT * FROM cte;`
   - Akibat: Tabel `cte` tidak teridentifikasi karena grammar tidak mengenal klausa `WITH`; matrix kosong atau salah.
   - Informasi yang dibutuhkan: Aturan grammar untuk `WITH` clause dan resolusi nama CTE sebagai sumber tabel.

2. **Query dinamis / string concatenation**
   - Contoh SQL: Query yang dibangun melalui variabel string pada runtime atau `EXECUTE` dengan string dinamis.
   - Akibat: Tabel yang terlibat tidak dapat dideteksi secara statis karena nama tabel hanya diketahui saat eksekusi; matrix tidak lengkap.
   - Informasi yang dibutuhkan: Analisis runtime atau eksekusi query aktual untuk melihat tabel yang benar-benar diakses.

3. **Tidak ada katalog skema database untuk resolusi nama ambigu**
   - Contoh SQL: `SELECT nama FROM pelanggan, pesanan` tanpa qualifier (`nama` ada di kedua tabel).
   - Akibat: Sistem hanya mencatat warning "ambigu tanpa skema" dan `resolved` tetap kosong; matrix tidak akurat.
   - Informasi yang dibutuhkan: Katalog skema database (daftar tabel dan kolom per tabel) atau constraint relasi antar tabel untuk resolved kolom ambigu.

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.

Jawab : 

| No | Nama | Todo | Bug | Dokumen | tests | data |
| 1  | Arya | T1, T2  | R1, R2, A1 | KARTU_DESAIN, LOG_AI, LAPORAN_BUG, LAPORAN_AKHIR | test_tambahan.py | |
| 2  | Fatur | T3   | L1, L2, L3, P1, P2, P3 | LOG_AI, LAPORAN_BUG, LAPORAN_AKHIR | test_tambahan.py  | ground_truth.csv |
