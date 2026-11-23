-- tabel master wilayah (kabupaten/kota) di katalog bersama. 1 baris = 1 kabupaten/kota.
-- wilayah_id = kode wilayah dari sumber.

CREATE SCHEMA IF NOT EXISTS lake.analytics;

DROP TABLE IF EXISTS lake.analytics.dim_wilayah;
CREATE TABLE lake.analytics.dim_wilayah AS
SELECT wilayah_id, kode_prov, provinsi, nama, jenis,
       penduduk, luas_km2, kepadatan_km2, luas_valid, wilayah_key
FROM lake.wilayah.clean_wilayah;

-- Cek: wilayah_id dan wilayah_key harus unik (kalau tidak, build berhenti dengan error)
SELECT CASE WHEN count(*) = count(DISTINCT wilayah_id) AND count(*) = count(DISTINCT wilayah_key)
            THEN 'OK dim_wilayah: ' || count(*) || ' baris, kunci unik'
            ELSE error('dim_wilayah: wilayah_id / wilayah_key tidak unik') END AS cek
FROM lake.analytics.dim_wilayah;
