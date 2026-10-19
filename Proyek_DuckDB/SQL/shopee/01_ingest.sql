CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.shopee;
CREATE TABLE raw.shopee AS
SELECT * FROM read_csv('DataRaw/raw_dataset_shopee.csv',
                       header = true, all_varchar = true);
