-- 02_staging.sql : STAGING layer. Teks jadi angka.
CREATE SCHEMA IF NOT EXISTS stg;

DROP TABLE IF EXISTS stg.shopee;
CREATE TABLE stg.shopee AS
SELECT
  'shopee'                                                                   AS marketplace,
  keyword                                                                    AS keyword_pencarian,
  trim(product_name)                                                         AS product_name,
  product_url,
  TRY_CAST(regexp_replace(price_discount_raw, '[^0-9]', '', 'g') AS BIGINT)  AS harga,
  TRY_CAST(regexp_replace(price_original_raw, '[^0-9]', '', 'g') AS BIGINT)  AS harga_asli,
  TRY_CAST(rating_raw AS DOUBLE)                                             AS rating,
  CASE
    WHEN sold_raw IS NULL THEN NULL
    WHEN upper(sold_raw) LIKE '%RB%'                                          -- '10RB+' = 10.000
      THEN TRY_CAST(regexp_extract(sold_raw, '(\d+)', 1) AS INTEGER) * 1000
    ELSE TRY_CAST(regexp_extract(sold_raw, '(\d+)', 1) AS INTEGER)
  END                                                                        AS terjual,
  seller_name,
  seller_location,
  TRY_CAST(scraped_at AS TIMESTAMP)                                          AS scraped_at
FROM raw.shopee;
