CREATE SCHEMA IF NOT EXISTS stg;

DROP TABLE IF EXISTS stg.tokopedia;
CREATE TABLE stg.tokopedia AS
SELECT
  'tokopedia'                                                                AS marketplace,
  keyword                                                                    AS search_phone,   -- nama kolom lama dipertahankan agar map_listing & mart tidak berubah
  trim(regexp_replace(product_name, '^[0-9]+%\s*', ''))                      AS product_name,
  product_url,
  TRY_CAST(regexp_replace(price_discount_raw, '[^0-9]', '', 'g') AS BIGINT)  AS harga,
  TRY_CAST(regexp_replace(price_original_raw, '[^0-9]', '', 'g') AS BIGINT)  AS harga_asli,
  TRY_CAST(rating_raw AS DOUBLE)                                             AS rating,
  CASE
    WHEN sold_raw IS NULL THEN NULL
    WHEN upper(sold_raw) LIKE '%RB%'                                          -- '10rb+' = 10.000
      THEN TRY_CAST(regexp_extract(sold_raw, '(\d+)', 1) AS INTEGER) * 1000
    ELSE TRY_CAST(regexp_extract(sold_raw, '(\d+)', 1) AS INTEGER)
  END                                                                        AS terjual,
  seller_name,
  seller_location,                                                           -- seller_city di CSV isinya sama persis, tidak dipakai
  TRY_CAST(scraped_at AS TIMESTAMP)                                          AS scraped_at
FROM raw.tokopedia;
