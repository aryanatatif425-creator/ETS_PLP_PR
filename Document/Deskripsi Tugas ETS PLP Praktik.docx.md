# **DESKRIPSI TUGAS ETS**

# **MATA KULIAH PROGRAMMING LANGUAGE PRAGMATICS**

# **Ekstraktor CRUD Matrix**

Codebase proyek kelompok (2 orang, 6 jam). Tool ini membaca file SQL dan menghasilkan **CRUD matrix**: tabel mana yang dibuat (C), dibaca (R), diubah (U), dan dihapus (D) oleh setiap file. Pipeline-nya mengikuti *Crafting Interpreters*: *lexer* (Bab 4), *grammar* dan AST (Bab 5), *parser* (Bab 6), dan *resolver* (Bab 11). *Codebase* ini **belum lengkap dan mengandung beberapa bug**. Tugas yang perlu diselesaikan, yaitu : melengkapinya, menemukan dan memperbaiki bug, membuktikan perbaikan dengan test, dan menjelaskan akar masalahnya memakai konsep dari bab-bab tersebut. *Codebase* yang dimaksud dapat diakses via [https\://s.id/FileSourceCode](https://s.id/FileSourceCode). Pengumpulan tugas paling lambat **Sabtu, 7 November 2026 Pukul 17.00 WIB via** [https\://s.id/PengupulanTugasETSPLPPraktik](https://s.id/PengupulanTugasETSPLPPraktik).  

## **Mulai**

python \-m pip install pytest  
python \-m pytest                                  \# test terlihat (sebagian gagal)  
python \-m crud.cli data/sample/\*.sql \--detail detail.csv \--kolom kolom.csv  
python \-m crud.cli data/sample/audit.sql \--ast    \# cetak AST hasil parsing dan resolusi  
python evaluate.py                                \# bandingkan parser vs regex

Butuh Python 3.10 atau lebih baru.

## **Struktur**

| Path | Isi |
| :---- | :---- |
| SPESIFIKASI.md | **Acuan kebenaran.** Aturan lexer, grammar, resolver, dan CRUD |
| crud/lexer.py | Lexer |
| crud/ast\_nodes.py | Node AST, iter\_nodes, pretty |
| crud/parser.py | Parser recursive descent |
| crud/resolver.py | Resolver scope dan alias |
| crud/analyzer.py | Aturan CRUD dan penggunaan kolom |
| crud/pipeline.py, crud/cli.py | Perangkai pipeline dan antarmuka baris perintah |
| baseline/regex\_extractor.py | Pembanding berbasis regex (sengaja naif, jangan diperbaiki) |
| evaluate.py | Precision dan recall parser vs regex |
| data/sample/\*.sql | Data uji |
| data/ground\_truth.csv | Label benar, **baru untuk 2 dari 4 file** |
| tests/ | Test terlihat |
| docs/ | Templat deliverable |

## 

## **Hal yang perlu diperhatikan**

1) Ada tiga bagian yang belum selesai, ditandai TODO(T1), TODO(T2), dan TODO(T3).  
2) Ada **beberapa bug**. Jumlahnya tidak diumumkan, dan tidak semuanya tertangkap test terlihat.  
3) Penilaian memakai **test tersembunyi** yang menguji SPESIFIKASI.md. Semua test terlihat lulus belum berarti pekerjaan selesai.  
4) Seperti di sistem legacy, komentar di kode bisa kurang tepat atau terlalu umum. Jika kode,komentar, dan spesifikasi berbeda, **\`SPESIFIKASI.md\` yang benar [https\://s.id/Spesifikasi\_md](https://s.id/Spesifikasi_md).**    
5) Jangan mengubah API publik (SPESIFIKASI.md bagian 7). Menambah fungsi, file, dan test boleh.  
6) Jangan mengubah test terlihat agar lulus. Saat penilaian, folder tests/ diganti dengan salinan asli.  
7) Lengkapi data/ground\_truth.csv untuk audit.sql dan pemeliharaan.sql **secara manual** berdasarkan spesifikasi, bukan dengan menyalin output tool kalian.

## **Aturan penggunaan AI**

AI dan coding agent **boleh** dipakai. Namun:

1) Setiap perbaikan harus bisa dijelaskan oleh **kedua** anggota. Di sesi demo, pengajar memilih siapa yang menjawab.  
2) Catat penggunaan AI di docs/LOG\_AI.md: apa yang diminta, apa yang diterima, diubah, atau ditolak, dan bagaimana kalian memverifikasinya.  
3) Bagian "akar masalah" di laporan bug harus ditulis dengan kata-kata sendiri dan memakai konsep dari buku. Bagian inilah yang diuji secara lisan.  
4) Kode *Crafting Interpreters* boleh dibaca. Struktur yang diadaptasi wajib diberi atribusi.

## ***Deliverable***

| No | Deliverable | Lokasi |
| :---: | ----- | ----- |
| 1 | Kode yang sudah diperbaiki dan dilengkapi, dengan commit dari kedua anggota | repositori Git |
| 2 | Satu entri laporan per bug yang ditemukan | docs/LAPORAN\_BUG.md |
| 3 | Lima keputusan desain beserta alternatif yang ditolak | docs/KARTU\_DESAIN.md |
| 4 | Test regresi untuk setiap bug, ditambah 5 test kasus tepi | tests/test\_tambahan.py |
| 5 | Label untuk audit.sql dan pemeliharaan.sql | data/ground\_truth.csv |
| 6 | Hasil evaluasi, analisis kesalahan regex, dan batas pendekatan | docs/LAPORAN\_AKHIR.md |
| 7 | Log penggunaan AI | docs/LOG\_AI.md |
| 8 | Demo 15 menit; setiap anggota diuji terpisah | sesi demo |

## **Rencana 6 jam (saran)**

| Jam | Kegiatan |
| :---- | :---- |
| 1 | Baca SPESIFIKASI.md. Jalankan test, CLI, dan \--ast pada semua file contoh. Catat setiap gejala yang aneh. |
| 2 | Lexer: perbaiki yang salah, selesaikan TODO yang ada di lexer. Tulis test regresi. |
| 3 | Parser: selesaikan TODO, cocokkan setiap fungsi dengan grammar di spesifikasi, periksa presedensi dan error recovery. |
| 4 | Resolver: selesaikan TODO, periksa aturan scope bagian 4 baris demi baris. |
| 5 | Analyzer dan data: periksa aturan CRUD bagian 5, labeli ground truth, jalankan evaluate.py. |
| 6 | Lengkapi laporan, kartu desain, dan log AI. Latih demo: saling menjelaskan bagian yang dikerjakan partner. |

Bekerjalah secara *pair programming* (bergantian *driver* dan *navigator* tiap 30 menit), bukan membagi modul, agar keduanya memahami seluruh kode.

## **Penilaian**

| Komponen | Bobot | Cara menilai |
| :---- | :---: | :---- |
| Bug diperbaiki | 25% | Test tersembunyi |
| TODO diselesaikan | 15% | Test tersembunyi |
| Laporan bug, kartu desain, test tambahan | 20% | Ketepatan akar masalah dan kualitas test |
| Demo individual | 35% | Prediksi output, modifikasi langsung, pertanyaan konsep |
| Log AI | 5% | Kejujuran dan bukti verifikasi |

## **Tips**

1) python \-m crud.cli FILE \--ast memperlihatkan pohon dan hasil resolusi (\-\> tabel).  
2) Bandingkan fungsi parser dengan aturan grammar satu per satu. Pertanyaan yang berguna: "apakah fungsi ini menerima semua yang diterima grammar, dan hanya itu?"  
3) Bug yang tidak mengubah CRUD matrix tetap bug jika melanggar spesifikasi.  
4) Satu gejala bisa disebabkan oleh lebih dari satu bug, dan satu bug bisa menimbulkan beberapa gejala. Cari akar masalahnya, jangan menambal gejalanya.