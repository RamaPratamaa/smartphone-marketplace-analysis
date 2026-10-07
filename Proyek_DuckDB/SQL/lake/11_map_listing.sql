-- petakan tiap listing marketplace ke phone_id.

CREATE SCHEMA IF NOT EXISTS lake.analytics;

DROP TABLE IF EXISTS lake.analytics.map_listing;
CREATE TABLE lake.analytics.map_listing AS
WITH listing AS (
  SELECT 'tokopedia' AS marketplace, product_url, product_name, search_phone AS keyword
  FROM lake.tokopedia.clean_listing
  UNION ALL
  SELECT 'shopee', product_url, product_name, keyword_pencarian
  FROM lake.shopee.clean_listing
),
tok AS (
  SELECT *,
    string_split(trim(regexp_replace(lower(replace(lower(product_name), '+', ' plus ')),
                                     '[^a-z0-9]+', ' ', 'g')), ' ') AS kata
  FROM listing
),
kandidat AS (
  SELECT t.marketplace, t.product_url, t.keyword, d.phone_id, d.phone_name,
         len(string_split(d.token_wajib, ' ')) AS jml_token,
         lower(d.phone_name) = lower(t.keyword) AS sama_keyword
  FROM tok t
  JOIN lake.analytics.dim_phone d
    -- token model harus muncul BERURUTAN dan berdampingan di judul listing
    -- (mencegah kata umum seperti 'air' atau 'pro' yang tersebar di judul jadi salah cocok)
    ON d.token_wajib <> ''
   AND contains(' ' || array_to_string(t.kata, ' ') || ' ', ' ' || d.token_wajib || ' ')
),
urut AS (
  SELECT *, row_number() OVER (
              PARTITION BY marketplace, product_url
              ORDER BY jml_token DESC, sama_keyword DESC, phone_id) AS rk,
            count(*) OVER (PARTITION BY marketplace, product_url, jml_token) AS jml_seri
  FROM kandidat
)
SELECT marketplace, product_url, phone_id, keyword,
       sama_keyword, jml_seri > 1 AS ambigu   -- TRUE = ada model lain yang sama spesifiknya (seri)
FROM urut
WHERE rk = 1;
