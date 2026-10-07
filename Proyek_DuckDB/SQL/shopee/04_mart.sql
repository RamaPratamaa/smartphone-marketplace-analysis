-- 04_mart.sql : MART layer. Ringkasan per keyword (sebelum dipetakan ke model).
CREATE SCHEMA IF NOT EXISTS mart;

DROP TABLE IF EXISTS mart.ringkasan_keyword;
CREATE TABLE mart.ringkasan_keyword AS
SELECT
  keyword_pencarian,
  count(*)               AS jumlah_listing,
  median(harga)          AS harga_median,
  sum(terjual)           AS total_terjual
FROM clean.shopee
WHERE harga_wajar AND bukan_aksesoris AND url_pertama
GROUP BY keyword_pencarian;
