-- Tabel ringkasan yang dibaca Streamlit.
CREATE SCHEMA IF NOT EXISTS mart;

DROP TABLE IF EXISTS mart.harga_model;
CREATE TABLE mart.harga_model AS
SELECT
  search_phone,
  count(*)                 AS jumlah_listing,
  median(harga)            AS harga_median,
  min(harga)               AS harga_min,
  max(harga)               AS harga_max,
  sum(terjual)             AS total_terjual,
  round(avg(rating), 2)    AS rating_rata2,
  round(avg(diskon_pct),1) AS diskon_rata2
FROM clean.tokopedia
WHERE harga_wajar AND bukan_aksesoris
GROUP BY search_phone;
