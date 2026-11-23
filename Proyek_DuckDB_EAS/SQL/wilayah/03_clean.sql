-- 03_clean.sql : CLEAN layer
-- Grain: 1 baris = 1 kabupaten/kota. Tidak ada baris dibuang; kualitas ditandai lewat flag.
CREATE SCHEMA IF NOT EXISTS clean;

DROP TABLE IF EXISTS clean.wilayah;
CREATE TABLE clean.wilayah AS
WITH dasar AS (
  SELECT *,
         -- beberapa nama berspasi ganda / berspasi di ujung ("Kabupaten  Merangin")
         trim(regexp_replace(nama, '\s+', ' ', 'g')) AS nama_bersih
  FROM stg.wilayah
)
SELECT
  kode                                             AS wilayah_id,   -- kode Kemendagri 4 digit
  kode_prov,
  trim(provinsi)                                   AS provinsi,
  nama_bersih                                      AS nama,
  CASE WHEN nama_bersih LIKE 'Kota%' THEN 'Kota' ELSE 'Kabupaten' END AS jenis,
  penduduk,
  luas                                             AS luas_raw,
  (luas IS NOT NULL AND luas > 0)                  AS luas_valid,   -- luas = 0 di beberapa baris (mis. Aceh Singkil)
  CASE WHEN luas > 0 THEN luas END                 AS luas_km2,
  CASE WHEN luas > 0 THEN round(penduduk / luas, 1) END AS kepadatan_km2,
  -- kunci pencocokan dengan teks lokasi marketplace:
  -- "Kota Administrasi Jakarta Barat" -> "kota jakarta barat"
  lower(regexp_replace(nama_bersih, '(Kota|Kabupaten) Administrasi', '\1')) AS wilayah_key
FROM dasar;
