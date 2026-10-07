CREATE SCHEMA IF NOT EXISTS mart;

DROP TABLE IF EXISTS mart.ringkasan_channel;
CREATE TABLE mart.ringkasan_channel AS
SELECT
  channel,
  count(*)                                   AS jumlah_komentar,
  count(*) FILTER (WHERE tipe_komentar = 'utama') AS komentar_utama,
  count(*) FILTER (WHERE tipe_komentar = 'reply') AS komentar_reply,
  round(avg(panjang), 1)                     AS rata2_panjang,
  sum(like_count)                            AS total_like,
  min(tanggal)::DATE                         AS tanggal_awal,
  max(tanggal)::DATE                         AS tanggal_akhir
FROM clean.youtube_komentar
WHERE NOT duplikat AND NOT terlalu_pendek AND NOT dari_pemilik_channel
GROUP BY channel;

DROP TABLE IF EXISTS mart.sebut_merek;
CREATE TABLE mart.sebut_merek AS
WITH merek(nama, pola) AS (
  VALUES
    ('Samsung',  'samsung|galaxy'),
    ('Apple',    'iphone|apple'),
    ('Xiaomi',   'xiaomi'),
    ('Redmi',    'redmi'),
    ('Poco',     'poco'),
    ('Oppo',     'oppo'),
    ('Vivo',     'vivo'),
    ('Realme',   'realme'),
    ('Infinix',  'infinix'),
    ('Tecno',    'tecno'),
    ('Google',   'pixel'),
    ('Asus ROG', '\brog\b')
)
SELECT
  m.nama                         AS merek,
  c.channel,
  count(*)                       AS jumlah_komentar,
  sum(c.like_count)              AS total_like
FROM clean.youtube_komentar c
JOIN merek m ON regexp_matches(lower(c.komentar), m.pola)
WHERE NOT c.duplikat AND NOT c.terlalu_pendek AND NOT c.dari_pemilik_channel
GROUP BY m.nama, c.channel;
