-- Ekstrak angka dari teks spesifikasi.
CREATE SCHEMA IF NOT EXISTS clean;

DROP TABLE IF EXISTS clean.gsmarena;
CREATE TABLE clean.gsmarena AS
WITH varian AS (
  -- satu baris per varian memori
  SELECT phone_id,
         unnest(string_split(internalmemory_raw, ',')) AS v
  FROM stg.gsmarena
),
mem AS (
  SELECT phone_id,
    -- penyimpanan
    TRY_CAST(regexp_extract(trim(v), '^(\d+)\s*(GB|TB)', 1) AS INTEGER)
      * CASE regexp_extract(trim(v), '^(\d+)\s*(GB|TB)', 2) WHEN 'TB' THEN 1024 ELSE 1 END AS storage_gb,
    TRY_CAST(regexp_extract(trim(v), '(\d+)\s*GB RAM', 1) AS INTEGER) AS ram_gb
  FROM varian
),
mem_agg AS (
  SELECT phone_id,
         min(storage_gb) AS storage_min_gb, max(storage_gb) AS storage_max_gb,
         min(ram_gb)     AS ram_min_gb,     max(ram_gb)     AS ram_max_gb,
         count(*)        AS jumlah_varian
  FROM mem GROUP BY phone_id
)
SELECT
  s.phone_id, s.brand, s.phone_name,
  s.chipset,
  m.ram_min_gb, m.ram_max_gb, m.storage_min_gb, m.storage_max_gb, m.jumlah_varian,
  -- baterai
  TRY_CAST(regexp_extract(s.battery_raw, '(\d+)\s*mAh', 1) AS INTEGER) AS battery_mah,
  s.release_year,
  s.gsmarena_url,
  s.chipset IS NULL                                        AS chipset_kosong,
  TRY_CAST(regexp_extract(s.battery_raw, '(\d+)\s*mAh', 1) AS INTEGER) IS NULL AS baterai_kosong
FROM stg.gsmarena s
LEFT JOIN mem_agg m USING (phone_id);
