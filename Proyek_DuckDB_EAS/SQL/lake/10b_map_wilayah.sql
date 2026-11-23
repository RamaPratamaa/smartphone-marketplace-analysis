-- jembatan teks lokasi penjual -> wilayah_id. 1 baris = 1 (marketplace, seller_location).
-- Lokasi yang tidak cocok tetap tampil dengan wilayah_id NULL supaya kelihatan apa yang perlu diperbaiki.
-- Aturan Shopee: "Kab. X" = Kabupaten X; tanpa awalan = Kota X; teks dalam kurung ("(Solo)") dibuang.
--
-- Tokopedia dan Shopee memakai aturan yang sama (keduanya menulis "Kab. X" untuk kabupaten).

CREATE SCHEMA IF NOT EXISTS lake.analytics;

DROP TABLE IF EXISTS lake.analytics.map_wilayah;
CREATE TABLE lake.analytics.map_wilayah AS
WITH lokasi AS (
  SELECT 'shopee' AS marketplace, seller_location, count(*) AS jumlah_listing
  FROM lake.shopee.clean_listing
  WHERE seller_location IS NOT NULL AND trim(seller_location) <> ''
  GROUP BY seller_location
  UNION ALL
  SELECT 'tokopedia', seller_location, count(*)
  FROM lake.tokopedia.clean_listing
  WHERE seller_location IS NOT NULL AND trim(seller_location) <> ''
  GROUP BY seller_location
),
bersih AS (
  SELECT *, trim(regexp_replace(seller_location, '\s*\(.*\)', '')) AS loc FROM lokasi
),
kunci AS (
  SELECT *,
         CASE WHEN loc ILIKE 'Kab. %' THEN 'kabupaten ' || lower(trim(substr(loc, 6)))
              WHEN loc ILIKE 'Kota %' THEN lower(loc)
              ELSE 'kota ' || lower(loc) END AS loc_key
  FROM bersih
)
SELECT
  k.marketplace,
  k.seller_location,
  w.wilayah_id,
  CASE WHEN w.wilayah_id IS NULL THEN 'tidak_ditemukan' ELSE 'exact_key' END AS match_method,
  w.nama AS nama_wilayah,
  k.jumlah_listing
FROM kunci k
LEFT JOIN lake.analytics.dim_wilayah w ON w.wilayah_key = k.loc_key;

-- Cek: 1 baris per (marketplace, seller_location)
SELECT CASE WHEN count(*) = count(DISTINCT (marketplace, seller_location))
            THEN 'OK map_wilayah: ' || count(*) || ' baris, ' || count(wilayah_id) || ' terpetakan'
            ELSE error('map_wilayah: duplikat (marketplace, seller_location)') END AS cek
FROM lake.analytics.map_wilayah;
