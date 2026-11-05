"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
from crud import ast_nodes as ast
from crud.analyzer import analyze_statement
from crud.parser import parse_sql
from crud.resolver import Resolver


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


