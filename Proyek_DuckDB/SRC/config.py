"""Konfigurasi pusat. Menambah sumber baru = tambah satu entri di SOURCES.

Dipakai oleh: build_local.py, publish.py, build_lake.py.
"""

# ---------- Katalog bersama (DuckLake) ----------
LAKE_CATALOG = "DuckLake/shared_catalog.ducklake"
LAKE_DATA = "DuckLake/lakehouse_storage/"

# SQL lintas sumber (jalan di katalog bersama, urut nama file)
SQL_LAKE_DIR = "SQL/lake"

# nama_sumber -> pengaturan
#   db      : database lokal sumber itu (tahap 1: build_local.py)
#   sql_dir : folder SQL yang dijalankan berurutan (01_, 02_, ...)
#   publish : daftar (tabel_lokal, nama_di_lake) yang disalin ke lake.<sumber>.<nama_di_lake>
#             (tahap 2: publish.py)
SOURCES = {
    "tokopedia": {
        "db": "DataBase/tokopedia_lokal.duckdb",
        "sql_dir": "SQL/tokopedia",
        "publish": [
            ("clean.tokopedia", "clean_listing"),
            ("mart.harga_model", "harga_model"),
        ],
    },
    "shopee": {
        "db": "DataBase/shopee_lokal.duckdb",
        "sql_dir": "SQL/shopee",
        "publish": [
            ("clean.shopee", "clean_listing"),
            ("mart.ringkasan_keyword", "ringkasan_keyword"),
        ],
    },
    "gsmarena": {
        "db": "DataBase/gsmarena_lokal.duckdb",
        "sql_dir": "SQL/gsmarena",  # huruf kecil, sama dengan nama folder di komputer Anda
        "publish": [
            ("clean.gsmarena", "clean_spek"),
            ("mart.spek_per_merek", "spek_per_merek"),
        ],
    },
    "youtube": {
        "db": "DataBase/youtube_lokal.duckdb",
        "sql_dir": "SQL/youtube",
        "publish": [
            ("clean.youtube_komentar", "clean_komentar"),
            ("mart.ringkasan_channel", "ringkasan_channel"),
            ("mart.sebut_merek", "sebut_merek"),
        ],
    },
    "wilayah": {
        "db": "DataBase/wilayah_lokal.duckdb",
        "sql_dir": "SQL/wilayah",
        "publish": [
            ("clean.wilayah", "clean_wilayah"),
        ],
    },
}
