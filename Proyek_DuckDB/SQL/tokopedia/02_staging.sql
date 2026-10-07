CREATE SCHEMA IF NOT EXISTS stg;

DROP TABLE IF EXISTS stg.tokopedia;
CREATE TABLE stg.tokopedia AS
SELECT
  'tokopedia'                                                                AS marketplace,
  search_phone,
  trim(regexp_replace(product_name, '^[0-9]+%\s*', ''))                      AS product_name,
  product_url,
  TRY_CAST(regexp_replace(price_discount_raw, '[^0-9]', '', 'g') AS BIGINT)  AS harga,
  TRY_CAST(regexp_replace(price_original_raw, '[^0-9]', '', 'g') AS BIGINT)  AS harga_asli,
  TRY_CAST(rating_raw AS DOUBLE)                                             AS rating,
  CASE
    WHEN sold_raw IS NULL THEN NULL
    WHEN sold_raw LIKE '%rb%'
      THEN TRY_CAST(regexp_extract(sold_raw, '(\d+)', 1) AS INTEGER) * 1000
    ELSE TRY_CAST(regexp_extract(sold_raw, '(\d+)', 1) AS INTEGER)
  END                                                                        AS terjual,
  seller_name
FROM raw.tokopedia;
