-- database lokal GSMArena
CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.gsmarena;
CREATE TABLE raw.gsmarena AS
SELECT * FROM read_csv('DataRaw/raw_dataset_gsmarena.csv',
                       header = true, all_varchar = true);
