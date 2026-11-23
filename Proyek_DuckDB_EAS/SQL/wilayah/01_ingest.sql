-- 01_ingest.sql : RAW layer (tabel referensi wilayah kabupaten/kota)
-- Sumber: data_wilayah.duckdb -> diekspor sekali ke DataRaw/data_wilayah.csv.
CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.wilayah;
CREATE TABLE raw.wilayah AS
SELECT * FROM read_csv('DataRaw/data_wilayah.csv', header = true, all_varchar = true);
