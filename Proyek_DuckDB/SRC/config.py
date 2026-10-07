LAKE_CATALOG = "DuckLake/shared_catalog.ducklake"
LAKE_DATA = "DuckLake/lakehouse_storage/"

# nama_sumber -> pengaturan
#   db      : file database lokal sumber itu
#   sql_dir : folder berisi SQL yang dijalankan berurutan (01_, 02_, ...)
#   publish : daftar (tabel di database lokal, nama tabel di katalog bersama)
SOURCES = {
    "tokopedia": {
        "db": "DataBase/tokopedia_lokal.duckdb",
        "sql_dir": "SQL/tokopedia",
        "publish": [
            ("clean.tokopedia", "clean_listing"),
            ("mart.harga_model", "harga_model"),
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
        "sql_dir": "SQL/gsmarena",
        "publish": [
            ("clean.gsmarena", "clean_spek"),
            ("mart.spek_per_merek", "spek_per_merek"),
        ],
    },
}

# Folder SQL lintas sumber (jalan di katalog DuckLake, setelah publish)
SQL_LAKE_DIR = "SQL/lake"
