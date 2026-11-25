-- 02_staging.sql : STAGING layer (ubah teks menjadi tipe data yang benar)
CREATE SCHEMA IF NOT EXISTS stg;

DROP TABLE IF EXISTS stg.wilayah;
CREATE TABLE stg.wilayah AS
SELECT
  TRY_CAST(kode AS INTEGER)                    AS kode,
  TRY_CAST(kode_prov AS INTEGER)               AS kode_prov,
  provinsi,
  nama,
  CAST(TRY_CAST(penduduk AS DOUBLE) AS BIGINT) AS penduduk,
  TRY_CAST(luas AS DOUBLE)                     AS luas
FROM raw.wilayah;
