-- satu baris per listing yang berhasil dipetakan ke model HP.
-- Gabungan Shopee + Tokopedia dengan skema seragam.
DROP TABLE IF EXISTS lake.analytics.fact_price;
CREATE TABLE lake.analytics.fact_price AS
WITH semua AS (
  SELECT 'tokopedia' AS marketplace, product_url, product_name, harga, harga_asli,
         rating, terjual, seller_name, harga_wajar, bukan_aksesoris, TRUE AS url_pertama
  FROM lake.tokopedia.clean_listing
  UNION ALL
  SELECT 'shopee', product_url, product_name, harga, harga_asli,
         rating, terjual, seller_name, harga_wajar, bukan_aksesoris, url_pertama
  FROM lake.shopee.clean_listing
)
SELECT
  m.phone_id, s.marketplace, s.product_url, s.product_name,
  s.harga, s.harga_asli, s.rating, s.terjual, s.seller_name,
  m.sama_keyword, m.ambigu,
  -- layak dianalisis: harga masuk akal, bukan aksesoris, bukan duplikat URL
  (s.harga_wajar AND s.bukan_aksesoris AND s.url_pertama) AS layak,
  -- pasti: tidak ada model lain yang sama spesifiknya, ATAU cocok dengan keyword pencarian
  (NOT m.ambigu OR m.sama_keyword) AS pasti
FROM semua s
JOIN lake.analytics.map_listing m USING (marketplace, product_url);
