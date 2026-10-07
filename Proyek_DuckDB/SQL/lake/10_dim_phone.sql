-- 10_dim_phone.sql : tabel master HP (dari GSMArena) di katalog bersama.
-- token_wajib = kata-kata yang HARUS ada di judul listing agar dianggap model ini.
-- (kata umum seperti 'galaxy', '5g', nama merek dibuang karena sering tidak ditulis penjual)
CREATE SCHEMA IF NOT EXISTS lake.analytics;

DROP TABLE IF EXISTS lake.analytics.dim_phone;
CREATE TABLE lake.analytics.dim_phone AS
SELECT
  phone_id, brand, phone_name, chipset,
  ram_min_gb, ram_max_gb, storage_min_gb, storage_max_gb,
  battery_mah, release_year,
  array_to_string(
    list_filter(
      string_split(trim(regexp_replace(lower(regexp_replace(replace(lower(phone_name), '+', ' plus '),
                                                            '\([^)]*\)', ' ', 'g')),
                                       '[^a-z0-9]+', ' ', 'g')), ' '),
      w -> w <> '' AND w NOT IN ('galaxy', '5g', '4g', 'lte', 'xiaomi') AND w <> lower(brand)),
    ' ') AS token_wajib
FROM lake.gsmarena.clean_spek;
