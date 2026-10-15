
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LAKE_CATALOG = str(ROOT / "lakehouse" / "shared_catalog.ducklake")
LAKE_DATA = str(ROOT / "lakehouse" / "shared_catalog.ducklake.files")


# nama_sumber -> pengaturan
#   db      : file database lokal sumber itu
#   sql_dir : folder berisi SQL yang dijalankan berurutan (01_, 02_, ...)
#   publish : daftar (tabel di database lokal, nama tabel di katalog bersama)
SOURCES = {
    "tokopedia": {
        "db": "database/tokopedia_lokal.duckdb",
        "sql_dir": "sql/tokopedia",
        "publish": [
            ("clean.tokopedia", "clean_listing"),
            ("mart.harga_model", "harga_model"),
        ],
    },
    "youtube": {
        "db": "database/youtube_lokal.duckdb",
        "sql_dir": "sql/youtube",
        "publish": [
            ("clean.youtube_komentar", "clean_komentar"),
            ("mart.ringkasan_channel", "ringkasan_channel"),
            ("mart.sebut_merek", "sebut_merek"),
        ],
    },
    "shopee": {
        "db": "database/shopee_lokal.duckdb",
        "sql_dir": "sql/shopee",
        "publish": [
            ("clean.shopee", "clean_listing"),
            ("mart.ringkasan_keyword", "ringkasan_keyword"),
        ],
    },
    "gsmarena": {
        "db": "database/gsmarena_lokal.duckdb",
        "sql_dir": "sql/gsmarena",
        "publish": [
            ("clean.gsmarena", "clean_spek"),
            ("mart.spek_per_merek", "spek_per_merek"),
        ],
    },
}

# Folder SQL lintas sumber (jalan di katalog DuckLake, setelah publish)
SQL_LAKE_DIR = "sql/lake"
