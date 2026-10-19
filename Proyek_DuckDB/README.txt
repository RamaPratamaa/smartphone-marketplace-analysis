ALUR: database lokal per sumber -> katalog DuckLake bersama -> tabel lintas sumber -> dashboard

Jalankan dari FOLDER UTAMA proyek:

1. pip install --upgrade duckdb streamlit pandas
2. python SRC/build_local.py   -> DataBase/<sumber>_lokal.duckdb (tokopedia, shopee, gsmarena, youtube)
3. python SRC/publish.py       -> DuckLake/shared_catalog.ducklake + lakehouse_storage/
4. python SRC/build_lake.py    -> lake.analytics (dim_phone, map_listing, fact_price, banding_harga)
5. streamlit run app/app.py

Struktur:
DataRaw/<sumber>/   data mentah per sumber
SQL/<sumber>/       01_ingest, 02_staging, 03_clean, 04_mart (jalan di database lokal)
SQL/lake/           10-13: SQL lintas sumber (jalan di katalog bersama)
SRC/config.py       daftar sumber
SRC/build_local.py  tahap 1
SRC/publish.py      tahap 2
SRC/build_lake.py   tahap 3
app/app.py          dashboard

Catatan:
 - Kunci penghubung antar sumber: phone_id (dari nama model GSMArena).
 - Listing Shopee/Tokopedia dipetakan ke phone_id lewat judul produk (SQL/lake/11_map_listing.sql),
   BUKAN dari keyword pencarian, karena hasil pencarian marketplace sering berisi produk lain.
 - Komentar YouTube belum bisa dipetakan ke phone_id (CSV tidak punya kolom video/model).
