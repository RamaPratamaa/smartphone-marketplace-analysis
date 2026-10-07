-- 04_mart.sql : MART layer. Ringkasan spesifikasi per merek.
CREATE SCHEMA IF NOT EXISTS mart;

DROP TABLE IF EXISTS mart.spek_per_merek;
CREATE TABLE mart.spek_per_merek AS
SELECT
  brand,
  count(*)                          AS jumlah_model,
  round(avg(battery_mah))           AS rata2_baterai_mah,
  round(avg(ram_max_gb), 1)         AS rata2_ram_max_gb,
  round(avg(storage_max_gb))        AS rata2_storage_max_gb
FROM clean.gsmarena
GROUP BY brand;
