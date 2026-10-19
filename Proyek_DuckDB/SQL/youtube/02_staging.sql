-- Rapikan nama kolom dan tipe data.
CREATE SCHEMA IF NOT EXISTS stg;

DROP TABLE IF EXISTS stg.youtube_komentar;
CREATE TABLE stg.youtube_komentar AS
SELECT
  row_number() OVER ()                                   AS komentar_id,   -- ID buatan, CSV tidak punya ID
  trim(Channel_Sumber)                                   AS channel,
  trim(Username)                                         AS username,
  Komentar                                               AS komentar_raw,
  TRY_CAST(Like_Count AS INTEGER)                        AS like_count,
  TRY_CAST(strptime(Tanggal, '%Y-%m-%dT%H:%M:%SZ') AS TIMESTAMP) AS tanggal,
  lower(nullif(trim(Tipe_Komentar), ''))                 AS tipe_komentar  -- 'utama' / 'reply' / NULL (Gadgetin tidak punya)
FROM raw.youtube_komentar;
