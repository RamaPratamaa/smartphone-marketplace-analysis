-- produk terjual per wilayah. 1 baris = 1 (kabupaten/kota, marketplace, merek).
-- Sumber: listing layak + pemetaan model pasti yang punya wilayah (lokasi TOKO penjual).
--   terjual_total  : jumlah 'terjual' yang tertulis di label marketplace, dijumlah per listing.
--                    Angka itu kumulatif seumur listing dan batas bawah ('1rb+' dihitung 1.000),
--                    bukan penjualan pada periode tertentu.
--   listing_ada_terjual : listing yang punya angka terjual. Listing tanpa label terjual tidak
--                    ikut dijumlah (bukan dianggap 0, tapi tidak diketahui).
CREATE SCHEMA IF NOT EXISTS lake.analytics;

DROP TABLE IF EXISTS lake.analytics.terjual_wilayah;
CREATE TABLE lake.analytics.terjual_wilayah AS
SELECT
  w.wilayah_id,
  w.provinsi,
  w.nama                                   AS kabupaten_kota,
  f.marketplace,
  p.brand,
  count(*)                                 AS listing,
  count(f.terjual)                         AS listing_ada_terjual,
  coalesce(sum(f.terjual), 0)              AS terjual_total,
  count(DISTINCT f.seller_name)            AS jumlah_toko,
  median(f.harga)                          AS harga_median
FROM lake.analytics.fact_price f
JOIN lake.analytics.dim_wilayah w USING (wilayah_id)
JOIN lake.analytics.dim_phone  p USING (phone_id)
WHERE f.layak AND f.pasti
GROUP BY ALL;
