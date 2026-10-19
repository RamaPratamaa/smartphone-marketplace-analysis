 CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.tokopedia;
CREATE TABLE raw.tokopedia AS
SELECT * FROM read_csv('DataRaw/checkpoint_tokopedia.csv', all_varchar = true);

SELECT * FROM raw.tokopedia LIMIT 10;
