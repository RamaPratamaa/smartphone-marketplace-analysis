CREATE SCHEMA IF NOT EXISTS clean;

DROP TABLE IF EXISTS clean.tokopedia;
CREATE TABLE clean.tokopedia AS
SELECT
  *,
  CASE WHEN harga_asli > harga
       THEN round(100.0 * (harga_asli - harga) / harga_asli, 1) END AS diskon_pct,
  (harga BETWEEN 300000 AND 90000000)                               AS harga_wajar,
  NOT regexp_matches(lower(product_name),
      'case|casing|softcase|tempered|charger|tws|earphone|headset|anti ?gores') AS bukan_aksesoris,
  -- URL yang sama muncul di beberapa keyword; hanya yang pertama dihitung (cegah penjualan terhitung ganda)
  row_number() OVER (PARTITION BY product_url ORDER BY scraped_at) = 1 AS url_pertama
FROM stg.tokopedia;
