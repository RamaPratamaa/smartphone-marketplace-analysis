-- Teks dibersihkan; baris ditandai, tidak dihapus.
CREATE SCHEMA IF NOT EXISTS clean;

DROP TABLE IF EXISTS clean.youtube_komentar;
CREATE TABLE clean.youtube_komentar AS
WITH teks AS (
  SELECT
    *,
    trim(regexp_replace(                       -- rapikan spasi berlebih
      regexp_replace(                          -- buang sisa tag HTML (<a ...>, </a>, dll)
        replace(replace(replace(replace(replace(replace(replace(
          komentar_raw,
          '<br>', ' '), '<br/>', ' '),         -- <br> jadi spasi
          '&quot;', '"'), '&#39;', ''''),      -- entitas HTML jadi karakter asli
          '&lt;', '<'), '&gt;', '>'), '&amp;', '&'),
        '<[^>]+>', ' ', 'g'),
      '\s+', ' ', 'g'))                        AS komentar
  FROM stg.youtube_komentar
)
SELECT
  *,
  length(komentar)                                                           AS panjang,
  row_number() OVER (PARTITION BY username, komentar, tanggal ORDER BY komentar_id) > 1
                                                                             AS duplikat,
  length(komentar) <= 3                                                      AS terlalu_pendek,
  lower(replace(channel, ' ', '')) = lower(replace(username, '@', ''))       AS dari_pemilik_channel
FROM teks;
