-- 13_mart_banding_harga.sql : perbandingan harga Shopee vs Tokopedia per model.
DROP TABLE IF EXISTS lake.analytics.banding_harga;
CREATE TABLE lake.analytics.banding_harga AS
WITH agg AS (
  SELECT
    phone_id,
    count(*) FILTER (WHERE marketplace = 'tokopedia')                 AS listing_tokopedia,
    count(*) FILTER (WHERE marketplace = 'shopee')                    AS listing_shopee,
    median(harga) FILTER (WHERE marketplace = 'tokopedia')            AS median_tokopedia,
    median(harga) FILTER (WHERE marketplace = 'shopee')               AS median_shopee,
    sum(terjual)  FILTER (WHERE marketplace = 'tokopedia')            AS terjual_tokopedia,
    sum(terjual)  FILTER (WHERE marketplace = 'shopee')               AS terjual_shopee
  FROM lake.analytics.fact_price
  WHERE layak AND pasti   -- hanya listing yang pemetaannya yakin
  GROUP BY phone_id
)
SELECT
  d.phone_id, d.brand, d.phone_name, d.release_year,
  d.ram_max_gb, d.storage_max_gb, d.battery_mah, d.chipset,
  a.listing_tokopedia, a.listing_shopee,
  a.median_tokopedia, a.median_shopee,
  a.median_shopee - a.median_tokopedia                               AS selisih_shopee_minus_tokopedia,
  round(100.0 * (a.median_shopee - a.median_tokopedia) / a.median_tokopedia, 1) AS selisih_pct,
  a.terjual_tokopedia, a.terjual_shopee,
  (a.listing_tokopedia >= 3 AND a.listing_shopee >= 3)               AS cukup_data
FROM agg a
JOIN lake.analytics.dim_phone d USING (phone_id);
