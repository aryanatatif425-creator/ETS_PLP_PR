"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud import ast_nodes as ast
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.pipeline import analyze_source
from crud.analyzer import analyze_statement
from crud.resolver import Resolver

# ===========================================================================
# Helper
# ===========================================================================

def one(sql):
    """Parse SQL, pastikan tepat satu statement tanpa error, kembalikan stmt."""
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    assert len(script.statements) == 1
    return script.statements[0]

# ==============================================================================
# 1. TEST REGRESI
# ==============================================================================

def test_regresi_r1_shadowing_alias_subquery():
    """Bug R1: Alias pada subquery dalam harus menutupi alias yang sama pada scope luar (shadowing).
    Sebelum perbaikan: _lookup() mencari dari terluar ke terdalam (reversed(chain)),
    sehingga x di subquery salah ter-resolve ke 'pelanggan' alih-alih 'pesanan'.
    """
    sql = "SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x WHERE x.total > 500000)"
    script = parse_sql(sql)
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    assert diags == []

    inner_select = script.statements[0].where.query
    inner_cols = [n for n in ast.iter_nodes(inner_select) if isinstance(n, ast.ColumnRef)]
    for col in inner_cols:
        if col.qualifier == "x":
            assert col.resolved == "pesanan"


def test_regresi_r2_kebocoran_scope_statement_delete():
    """Bug R2: Statement DELETE tidak memanggil _pop(), sehingga aliasnya bocor ke statement berikutnya.
    Menurut SPESIFIKASI.md 4.5: Setiap statement berdiri sendiri. Alias dari DELETE sebelumnya
    tidak boleh terlihat oleh statement berikutnya, dan rujukan ke alias tersebut harus menghasilkan error.
    """
    sql = """
    DELETE FROM sesi s WHERE s.kedaluwarsa < :sekarang;
    SELECT s.id FROM pengguna u WHERE u.aktif = 1;
    """
    script = parse_sql(sql)
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    # Statement kedua harus menghasilkan diagnostic error bahwa alias 's' tidak terdefinisi
    assert any(d.level == "error" and "'s'" in d.message for d in diags)
    stmt2_cols = [n for n in ast.iter_nodes(script.statements[1]) if isinstance(n, ast.ColumnRef) and n.qualifier == "s"]
    assert stmt2_cols[0].resolved is None


def test_regresi_a1_subquery_update_selalu_read():
    """Bug A1: Subquery pada klausa SET dan WHERE di statement UPDATE harus ditandai operasi R, bukan U.
    Menurut SPESIFIKASI.md Bagian 5:
    'UPDATE | target: U | Tabel lain (subquery di SET maupun WHERE): R'
    'Membaca tabel lewat subquery selalu R, apa pun jenis statement luarnya.'
    Sebelum perbaikan: analyzer memanggil _collect(..., 'U'), sehingga tabel di subquery (pelanggan) salah ditandai U.
    """
    sql = "UPDATE pesanan SET status = 'BATAL' WHERE pelanggan_id IN (SELECT id FROM pelanggan WHERE diblokir = 1)"
    script = parse_sql(sql)
    assert script.errors == []
    usage = analyze_statement(script.statements[0])
    assert usage["pesanan"] == {"U"}
    assert usage["pelanggan"] == {"R"}

# ---------------------------------------------------------------------------
# Bug 4 – BUG(L1): Keyword Huruf Kecil Dianggap Identifier
# Sebelum perbaikan: 'select', 'from', dll. menghasilkan token IDENT bukan KEYWORD
# ---------------------------------------------------------------------------

def test_regresi_keyword_huruf_kecil_dan_campuran():
    """
    Kata kunci SQL bersifat case-insensitive (SPESIFIKASI.md §2.2).
    Lexer harus mengenali 'select', 'Select', dan 'SeLeCt' semua sebagai
    KEYWORD dengan nilai ternormalisasi ke huruf besar.
    """
    kasus = ["select", "Select", "SeLeCt", "FROM", "from", "FrOm",
             "where", "WHERE", "insert", "update", "delete"]
    for kata in kasus:
        toks = tokenize(kata)
        assert toks[0].type == T.KEYWORD, (
            f"'{kata}' harus dikenali sebagai KEYWORD, bukan {toks[0].type}"
        )
        assert toks[0].value == kata.upper(), (
            f"nilai token '{kata}' harus dinormalisasi ke '{kata.upper()}', "
            f"bukan '{toks[0].value}'"
        )

    # Query utuh dengan huruf kecil harus bisa di-parse tanpa error
    stmt = one("select id from pelanggan where aktif = 1;")
    assert isinstance(stmt, ast.Select)
    assert stmt.sources[0].name == "pelanggan"


# ---------------------------------------------------------------------------
# Bug 5 – BUG(L2): Operator <> Tidak Dikenali (Maximal Munch)
# Sebelum perbaikan: '<>' dipecah jadi dua token '<' dan '>', parser crash
# ---------------------------------------------------------------------------

def test_regresi_operator_tidak_sama_dengan():
    """
    Operator '<>' harus jadi satu token OP bernilai '<>' (SPESIFIKASI.md §2.5).
    Prinsip Maximal Munch: scanner selalu mengambil token terpanjang yang valid.
    """
    toks = [t for t in tokenize("a <> b") if t.type != T.EOF]
    op_tokens = [t for t in toks if t.type == T.OP]
    assert len(op_tokens) == 1, "harus ada tepat satu token OP"
    assert op_tokens[0].value == "<>", (
        f"nilai token OP harus '<>', bukan '{op_tokens[0].value}'"
    )

    # Harus bisa di-parse dalam query lengkap tanpa error
    stmt = one("SELECT 1 FROM t WHERE a <> 1;")
    assert isinstance(stmt.where, ast.BinaryOp)
    assert stmt.where.op == "<>"


# ---------------------------------------------------------------------------
# Bug 6 – BUG(L3): Karakter Kutip Lolos (Escaped Quotes) pada String Literal
# Sebelum perbaikan: 'O''Brien' terpotong jadi 'O', sisa teks crash parser
# ---------------------------------------------------------------------------

def test_regresi_string_escaped_quote():
    """
    Dua kutip berturut-turut ('') di dalam string mewakili satu karakter kutip
    (SPESIFIKASI.md §2.4). 'O''Brien' harus jadi satu token STRING = "O'Brien".
    """
    toks = tokenize("'O''Brien'")
    assert toks[0].type == T.STRING, "harus menghasilkan token STRING"
    assert toks[0].value == "O'Brien", (
        f"nilai string setelah unescape harus \"O'Brien\", bukan '{toks[0].value}'"
    )

    # Kutip ganda di awal
    assert tokenize("'''awal'")[0].value == "'awal"
    # Kutip ganda di akhir
    assert tokenize("'akhir'''")[0].value == "akhir'"
    # Hanya kutip ganda
    assert tokenize("''''")[0].value == "'"

    # Harus bisa di-parse dalam query lengkap
    stmt = one("SELECT id FROM t WHERE nama = 'O''Brien';")
    assert isinstance(stmt.where, ast.BinaryOp)
    right = stmt.where.right
    assert isinstance(right, ast.Literal) and right.value == "O'Brien"


# ---------------------------------------------------------------------------
# Bug 7 – BUG(P1): Presedensi Logika AND dan OR Disamakan
# Sebelum perbaikan: 'a OR b AND c' diparsing menjadi '(a OR b) AND c'
# ---------------------------------------------------------------------------

def test_regresi_presedensi_and_or():
    """
    AND memiliki presedensi lebih tinggi dari OR (SPESIFIKASI.md §3.1):
    'a=1 OR b=2 AND c=3' harus diparsing menjadi 'a=1 OR (b=2 AND c=3)',
    yaitu root AST-nya adalah node OR, bukan AND.
    """
    stmt = one("SELECT 1 FROM t WHERE a = 1 OR b = 2 AND c = 3;")
    where = stmt.where

    # Root harus OR
    assert isinstance(where, ast.BinaryOp), "where harus BinaryOp"
    assert where.op == "OR", (
        f"root operator harus 'OR' (AND lebih terikat), bukan '{where.op}'"
    )

    # Cabang kanan dari OR harus AND
    assert isinstance(where.right, ast.BinaryOp), "cabang kanan OR harus BinaryOp"
    assert where.right.op == "AND", (
        f"cabang kanan harus 'AND', bukan '{where.right.op}'"
    )

    # Cabang kiri OR harus perbandingan sederhana (bukan OR/AND lagi)
    assert isinstance(where.left, ast.BinaryOp)
    assert where.left.op == "="

    # Kasus berantai: a OR b OR c AND d  =>  (a OR b) OR (c AND d)
    stmt2 = one("SELECT 1 FROM t WHERE a=1 OR b=2 OR c=3 AND d=4;")
    root = stmt2.where
    assert root.op == "OR"
    assert root.right.op == "AND"


# ---------------------------------------------------------------------------
# Bug 8 – BUG(P2): Parsing LEFT OUTER JOIN Menolak Keyword Opsional OUTER
# Sebelum perbaikan: 'LEFT OUTER JOIN' membuang ParseError karena OUTER tidak dikonsumsi
# ---------------------------------------------------------------------------

def test_regresi_left_outer_join():
    """
    Grammar SQL menyatakan OUTER adalah opsional setelah LEFT (SPESIFIKASI.md §3):
    'join = [ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN" ...'
    'LEFT OUTER JOIN' harus berhasil di-parse dan kind-nya tetap "LEFT".
    """
    stmt = one("SELECT * FROM a LEFT OUTER JOIN b ON b.id = a.id;")
    assert len(stmt.joins) == 1, "harus ada tepat satu JOIN"
    join = stmt.joins[0]
    assert join.kind == "LEFT", (
        f"kind join harus 'LEFT', bukan '{join.kind}'"
    )
    assert join.source.name == "b"

    # Pastikan juga LEFT JOIN (tanpa OUTER) tetap berjalan normal
    stmt2 = one("SELECT * FROM a LEFT JOIN b ON b.id = a.id;")
    assert stmt2.joins[0].kind == "LEFT"

    # INNER JOIN juga tidak terpengaruh
    stmt3 = one("SELECT * FROM a INNER JOIN b ON b.id = a.id;")
    assert stmt3.joins[0].kind == "INNER"


# ---------------------------------------------------------------------------
# Bug 9 – BUG(P3): Panic Mode Recovery Membuang Sisa File Sampai EOF
# Sebelum perbaikan: satu syntax error menghilangkan seluruh statement sesudahnya
# ---------------------------------------------------------------------------

def test_regresi_panic_mode_recovery():
    """
    Setelah error sintaks, parser harus membuang token hanya hingga ';' berikutnya
    dan melanjutkan parsing statement valid setelahnya (SPESIFIKASI.md §6).
    """
    sql = (
        "SELECT id, FROM tabel_rusak;\n"       # baris 1: syntax error
        "SELECT id FROM tabel_valid;\n"         # baris 2: valid
        "UPDATE produk SET stok = 0;\n"         # baris 3: valid
        "DELETE FROM keranjang WHERE 1=1;\n"    # baris 4: valid
    )
    result = analyze_source(sql)

    # Tepat satu error (dari statement rusak)
    assert len(result.parse_errors) == 1, (
        f"harus ada tepat 1 parse error, bukan {len(result.parse_errors)}"
    )

    # Tiga statement valid harus tetap terproses
    assert len(result.statements) == 3, (
        f"harus ada 3 statement valid, bukan {len(result.statements)}"
    )

    # Tabel dari statement valid harus muncul di matriks
    matrix = result.matrix()
    assert "tabel_valid" in matrix, "tabel_valid harus muncul di matriks CRUD"
    assert "produk" in matrix, "produk harus muncul di matriks CRUD"
    assert "keranjang" in matrix, "keranjang harus muncul di matriks CRUD"

    # Operasi harus benar
    assert matrix["tabel_valid"] == "R"
    assert matrix["produk"] == "U"
    assert matrix["keranjang"] == "D"

# ==============================================================================
# 2. TEST KASUS TEPI & FITUR RESOLVER (TODO T2 / VALIDASI)
# ==============================================================================

def test_kolom_tanpa_qualifier_ambigu_dua_tabel():
    """Kasus Tepi 1 (TODO T2): Dua tabel di FROM (pelanggan, pesanan) tanpa qualifier.
    Kolom 'status' tidak jelas milik tabel mana tanpa skema DB, sehingga harus menghasilkan
    warning 'kolom 'status' ambigu tanpa skema' dan resolved tetap None (SPESIFIKASI.md 4.3).
    """
    sql = "SELECT status FROM pelanggan p, pesanan o"
    script = parse_sql(sql)
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    assert any(d.level == "warning" and "ambigu tanpa skema" in d.message for d in diags)
    col = [n for n in ast.iter_nodes(script) if isinstance(n, ast.ColumnRef)][0]
    assert col.resolved is None


def test_subquery_from_dengan_alias_format():
    """Kasus Tepi 2: Subquery di FROM dengan alias harus di-resolve ke format '<subquery alias>'
    (SPESIFIKASI.md Bagian 4.2 & 4.3).
    """
    sql = "SELECT sub.total FROM (SELECT id, total FROM pesanan) sub"
    script = parse_sql(sql)
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    assert diags == []
    col = [n for n in ast.iter_nodes(script.statements[0].columns) if isinstance(n, ast.ColumnRef)][0]
    assert col.resolved == "<subquery sub>"

# ===========================================================================
# 3.TEST KASUS TEPI  –  semuanya berkaitan dengan TODO(T3): komentar blok /* ... */
# (SPESIFIKASI.md §2.3)
# ===========================================================================

def test_tepi_komentar_blok_satu_baris():
    """
    Risiko: komentar blok yang buka dan tutup ada di baris yang sama bisa
    terlewat oleh implementasi yang hanya melacak newline. Scanner harus
    membuang seluruh /* ... */ tanpa menghasilkan token.
    """
    toks = [t for t in tokenize("/* ini komentar */ SELECT") if t.type != T.EOF]
    assert len(toks) == 1
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"


def test_tepi_komentar_blok_multi_baris():
    """
    Risiko: komentar blok lintas baris perlu memperbarui nomor baris dengan
    benar agar posisi token setelahnya akurat. Token SELECT harus ada di baris 3.
    """
    src = "/*\n   baris dua\n*/ SELECT"
    toks = [t for t in tokenize(src) if t.type != T.EOF]
    assert len(toks) == 1
    assert toks[0].type == T.KEYWORD and toks[0].line == 3, (
        f"SELECT harus di baris 3, bukan baris {toks[0].line}"
    )


def test_tepi_komentar_blok_berisi_bintang():
    """
    Risiko: karakter '*' di dalam komentar blok bisa salah dianggap penutup
    jika implementasi hanya cek karakter satu per satu (misalnya '*/a/' bukan '*/').
    Spesifikasi §2.3 menyebut 'boleh berisi *'.
    """
    # Bintang tunggal di tengah komentar, bukan penutup
    toks = [t for t in tokenize("/* a * b */ SELECT") if t.type != T.EOF]
    assert len(toks) == 1 and toks[0].value == "SELECT"

    # Dua bintang berturut-turut juga bukan penutup
    toks2 = [t for t in tokenize("/* a ** b */ SELECT") if t.type != T.EOF]
    assert len(toks2) == 1 and toks2[0].value == "SELECT"


def test_tepi_komentar_blok_tidak_ditutup():
    """
    Risiko: komentar blok yang tidak ditutup harus menghasilkan LexError
    (SPESIFIKASI.md §2.3), bukan membiarkan parser menerima input kosong/salah.
    """
    with pytest.raises(LexError) as info:
        tokenize("SELECT /* komentar tak berakhir")
    # Pesan error harus mencantumkan posisi pembuka komentar, bukan EOF acak
    assert info.value.line >= 1


def test_tepi_komentar_blok_langsung_menempel_token():
    """
    Risiko: tanpa spasi antara komentar dan token berikutnya (/*x*/SELECT),
    scanner yang naif bisa gagal memisahkan keduanya atau menghasilkan
    token dengan nilai yang salah.
    """
    # Tanpa spasi di antara komentar dan keyword
    toks = [t for t in tokenize("/*komentar*/SELECT") if t.type != T.EOF]
    assert len(toks) == 1
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"

    # Komentar di antara dua identifier tanpa spasi
    toks2 = [t for t in tokenize("SELECT/*komentar*/id FROM t") if t.type != T.EOF]
    types_ = [t.type for t in toks2]
    assert types_ == [T.KEYWORD, T.IDENT, T.KEYWORD, T.IDENT]
