-- 01_ingest.sql : RAW layer (database lokal YouTube)
CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.youtube_komentar;
CREATE TABLE raw.youtube_komentar AS
SELECT * FROM read_csv('DataRaw/DATASET_KOMEN_4_CHANNEL.csv',
                       header = true, all_varchar = true);
