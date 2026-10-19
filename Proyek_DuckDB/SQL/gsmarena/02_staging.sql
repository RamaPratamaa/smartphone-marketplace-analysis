-- Tipe data dan kunci model.
CREATE SCHEMA IF NOT EXISTS stg;

DROP TABLE IF EXISTS stg.gsmarena;
CREATE TABLE stg.gsmarena AS
SELECT
  -- phone_id = kunci penghubung antar sumber (contoh: 'samsung_galaxy_a57')
  -- '+' ditulis 'plus' supaya 'Pro' dan 'Pro+' tidak kembar
  trim(both '_' FROM regexp_replace(replace(lower(phone_name), '+', ' plus'), '[^a-z0-9]+', '_', 'g')) AS phone_id,
  trim(brand)                         AS brand,
  trim(phone_name)                    AS phone_name,
  chipset_raw                         AS chipset,
  internalmemory_raw,
  battery_raw,
  released_raw,
  TRY_CAST(release_year AS INTEGER)   AS release_year,
  gsmarena_url,
  TRY_CAST(scraped_at AS TIMESTAMP)   AS scraped_at
FROM raw.gsmarena;
