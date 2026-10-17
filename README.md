# 📱 Analisis Harga dan Spesifikasi Smartphone di Marketplace Indonesia

Project **PJBL Data Mining II** ini mengintegrasikan data spesifikasi smartphone dari **GSMArena**, listing harga dari **Tokopedia** dan **Shopee**, serta komentar YouTube. Pipeline menggunakan **DuckDB** untuk pengolahan data per sumber, **DuckLake** sebagai katalog lakehouse bersama dengan data fisik Parquet, SQL untuk transformasi, dan **Streamlit** untuk dashboard analitik.

> Fokus implementasi yang tersedia saat ini adalah pemetaan listing marketplace ke model HP, analisis harga dan listing, hubungan spesifikasi dengan harga, serta analisis komentar dan penyebutan merek di YouTube.

---

## 🎯 Tujuan Project

Project ini membangun alur **data ingestion → ETL per sumber → publikasi ke DuckLake → integrasi lintas sumber → analytics → dashboard** untuk membantu menjawab pertanyaan:

- Berapa median harga smartphone yang sama di Tokopedia dan Shopee?
- Berapa selisih harga antarmarketplace untuk model yang tersedia di kedua platform?
- Berapa banyak listing yang dapat dipetakan secara meyakinkan ke model HP tertentu?
- Bagaimana harga listing bervariasi menurut merek dan spesifikasi?
- Kata atau merek apa yang sering disebut dalam komentar YouTube yang tersedia?
- Seberapa banyak data yang lolos pemeriksaan kualitas dan dapat digunakan dalam analisis?

Analisis perbandingan harga hanya mewakili listing yang berhasil dikumpulkan, dipetakan, dan lolos filter kualitas. Hasilnya tidak otomatis mewakili seluruh harga di marketplace.

## 👥 Anggota Tim

| Nama | Tugas Utama |
|---|---|
| Rama | Mengembangkan modul web scraping dan akuisisi data dari setiap sumber, serta merancang dan membangun database DuckDB terpisah untuk masing-masing dataset sebagai penyimpanan hasil ekstraksi. |
| Yudha | Mengembangkan pipeline pengolahan dan integrasi data menggunakan SQL, DuckDB, dan DuckLake, meliputi transformasi, pembersihan, standardisasi, pemetaan listing ke model smartphone, validasi kualitas data, serta analisis komparatif harga. |
| Firqi | Merancang dan mengembangkan dashboard analitik interaktif menggunakan Streamlit dan Plotly, mengintegrasikan tabel analitik dari DuckLake, serta menyajikan ringkasan data, perbandingan harga marketplace, hubungan spesifikasi dengan harga, ringkasan komentar, dan indikator kualitas data. |

> Mata kuliah: **Data Mining II** — Semester 7

---

## 📦 Sumber Data

### 1. GSMArena — spesifikasi smartphone

- **Sumber:** [gsmarena.com](https://www.gsmarena.com)
- **CSV:** `data/raw_dataset_gsmarena.csv`
- **Database hasil pipeline lokal:** `database/gsmarena_lokal.duckdb`
- **Proses scraping/dokumentasi:** `notebook/01_scraping_gsmarena.ipynb`

Data mencakup identitas model dan atribut spesifikasi yang tersedia, seperti merek, nama HP, chipset, RAM, penyimpanan, baterai, tahun rilis, URL, dan waktu scraping. SQL clean membentuk `phone_id`, mengurai beberapa atribut numerik, serta menyiapkan tabel bersih dan ringkasan spesifikasi per merek.

### 2. Tokopedia — listing dan harga

- **Sumber:** [tokopedia.com](https://www.tokopedia.com)
- **CSV:** `data/raw_dataset_tokopedia.csv`
- **Database pipeline lokal:** `database/tokopedia_lokal.duckdb`
- **Notebook:** `notebook/02_scraping_tokopedia.ipynb`

Data berisi judul produk, URL, keyword pencarian, harga saat ini/harga asli, rating, jumlah terjual, informasi penjual, dan waktu scraping. SQL staging/clean mengubah harga dan atribut teks menjadi nilai yang dapat dianalisis, menghitung diskon, dan menandai harga yang wajar serta kemungkinan listing aksesori.

### 3. Shopee — listing dan harga

- **Sumber:** [shopee.co.id](https://shopee.co.id)
- **CSV:** `data/raw_dataset_shopee.csv`
- **Database pipeline lokal:** `database/shopee_lokal.duckdb`
- **Notebook:** `notebook/03_scraping_shopee.ipynb`

Struktur datanya serupa dengan Tokopedia, tetapi terdapat perbedaan kolom dan proses deteksi URL berulang yang ditangani oleh SQL sumber dan SQL lakehouse. Metode scraping dan jumlah listing dapat berubah sesuai data yang berhasil dikumpulkan.

### 4. YouTube — komentar

- **CSV:** `data/DATASET_KOMEN_4_CHANNEL.csv`
- **Database pipeline lokal:** `database/youtube_lokal.duckdb`
- **Notebook scraping khusus:** tidak ada pada daftar notebook saat ini; proses ETL komentar tersedia di `sql/youtube/`.

SQL YouTube membersihkan teks komentar, menandai komentar duplikat/terlalu pendek dan komentar pemilik channel, lalu membentuk ringkasan per channel serta jumlah penyebutan merek. **SQL yang tersedia tidak menghasilkan label sentimen positif, netral, atau negatif.** Oleh karena itu, hasil analisis YouTube harus disebut sebagai analisis komentar/penyebutan merek, bukan hasil model sentimen.

> Jumlah baris pada CSV dan database dapat berbeda karena file data bisa diperbarui. Untuk angka aktual, jalankan pipeline dan gunakan jumlah baris yang tercetak saat build, bukan menganggap angka lama di dokumentasi selalu berlaku.

---

## 🏗️ Arsitektur dan Alur Data

```text
CSV sumber / data hasil scraping
        │
        ▼
notebook/01–03 (pengambilan/eksplorasi data)
        │
        ▼
SRC/build_local.py + SQL per sumber
        │
        ├── database/gsmarena_lokal.duckdb
        ├── database/tokopedia_lokal.duckdb
        ├── database/shopee_lokal.duckdb
        └── database/youtube_lokal.duckdb
        │
        ▼
SRC/publish.py
Menyalin tabel terpilih ke katalog DuckLake bersama
        │
        ▼
lake.<sumber>.<tabel>
        │
        ▼
SRC/build_lake.py + sql/lake/10–13
        │
        ▼
lake.analytics.dim_phone
lake.analytics.map_listing
lake.analytics.fact_price
lake.analytics.banding_harga
        │
        ▼
dashboard/dashboard.py (Streamlit)
```

Pipeline yang dijalankan dari folder root project:

1. `python SRC/build_local.py` — menjalankan SQL sumber untuk semua database lokal.
2. `python SRC/publish.py` — memublikasikan tabel terpilih dari database lokal ke DuckLake.
3. `python SRC/build_lake.py` — membangun tabel analitik lintas sumber di DuckLake.
4. `python -m streamlit run dashboard/dashboard.py` — menjalankan dashboard.

Untuk membangun satu sumber saja, gunakan misalnya `python SRC/build_local.py --source tokopedia`. Pilihan sumber yang tersedia adalah `tokopedia`, `shopee`, `gsmarena`, dan `youtube`.

### Peran folder utama

| Folder | Tanggung jawab |
|---|---|
| `data/` | CSV sumber yang digunakan oleh query ingest. |
| `database/` | Database DuckDB lokal per sumber, termasuk database hasil pipeline dengan akhiran `_lokal`. Beberapa file database lain juga ada di arsip dan tidak otomatis menjadi input pipeline `SRC/`. |
| `SRC/` | Mengatur build lokal, publikasi tabel, dan build tabel analitik lakehouse. |
| `sql/` | Berisi query ETL untuk tiap sumber dan query integrasi lintas sumber. |
| `lakehouse/` | Katalog DuckLake dan folder data fisik yang dikelola DuckLake. |
| `dashboard/` | Antarmuka analitik Streamlit. |
| `notebook/` | Notebook scraping dan notebook pembangunan/eksplorasi DuckLake. |

---

## 🧱 ETL Per Sumber: `SRC/` dan `sql/`

### `SRC/config.py`

Pusat konfigurasi untuk:

- `LAKE_CATALOG`: path katalog bersama `lakehouse/shared_catalog.ducklake`.
- `LAKE_DATA`: path penyimpanan data fisik DuckLake, yaitu `lakehouse/shared_catalog.ducklake.files/`.
- `SOURCES`: database lokal, folder SQL, dan tabel yang dipublikasikan untuk masing-masing sumber.
- `SQL_LAKE_DIR`: folder query integrasi lintas sumber (`sql/lake`).

Konfigurasi publikasi saat ini:

| Sumber | Database lokal | Tabel lokal → tabel di DuckLake |
|---|---|---|
| Tokopedia | `database/tokopedia_lokal.duckdb` | `clean.tokopedia` → `lake.tokopedia.clean_listing`; `mart.harga_model` → `lake.tokopedia.harga_model` |
| Shopee | `database/shopee_lokal.duckdb` | `clean.shopee` → `lake.shopee.clean_listing`; `mart.ringkasan_keyword` → `lake.shopee.ringkasan_keyword` |
| GSMArena | `database/gsmarena_lokal.duckdb` | `clean.gsmarena` → `lake.gsmarena.clean_spek`; `mart.spek_per_merek` → `lake.gsmarena.spek_per_merek` |
| YouTube | `database/youtube_lokal.duckdb` | `clean.youtube_komentar` → `lake.youtube.clean_komentar`; `mart.ringkasan_channel` → `lake.youtube.ringkasan_channel`; `mart.sebut_merek` → `lake.youtube.sebut_merek` |

### `SRC/build_local.py`

Mencari file `.sql` di folder sumber sesuai urutan nama (`01_`, `02_`, dan seterusnya), membuka database lokal DuckDB, lalu menjalankan query satu per satu. Program mencetak tabel yang ditemukan beserta jumlah barisnya. SQL sumber menggunakan pola pembuatan ulang tabel, sehingga build ulang menghitung ulang tabel dari CSV sumber.

### Empat tahap SQL sumber

Setiap sumber memiliki pola empat file:

| File | Fungsi umum |
|---|---|
| `01_ingest.sql` | Membaca CSV ke tabel `raw`. |
| `02_staging.sql` | Menstandarkan kolom dan mengonversi tipe data. |
| `03_clean.sql` | Menambahkan hasil pembersihan dan penanda kualitas. Penanda tidak selalu berarti baris langsung dihapus. |
| `04_mart.sql` | Membuat ringkasan agregat untuk kebutuhan analisis. |

Rincian per sumber:

- **`sql/gsmarena/`**: membangun `raw.gsmarena`, tabel staging/clean spesifikasi, dan `mart.spek_per_merek`.
- **`sql/tokopedia/`**: mengurai harga, rating dan jumlah terjual; menandai harga wajar/kemungkinan aksesori; membentuk `mart.harga_model`.
- **`sql/shopee/`**: melakukan transformasi serupa untuk Shopee dan membentuk `mart.ringkasan_keyword`; kolom tertentu seperti `url_pertama` digunakan untuk menandai URL pertama/duplikasi.
- **`sql/youtube/`**: membersihkan komentar, memberi penanda kualitas, dan membentuk `mart.ringkasan_channel` serta `mart.sebut_merek`.

### `SRC/publish.py`

Membuka katalog DuckLake, memasang database lokal sebagai sumber baca, membuat schema sumber di katalog bersama, lalu menyalin tabel yang ditetapkan di `SOURCES`. Tabel tujuan dihapus dan dibuat ulang sebelum data disalin. Artinya, proses publikasi ini merupakan **full refresh**, bukan sinkronisasi inkremental.

### `SRC/build_lake.py`

Menjalankan seluruh SQL di `sql/lake/` secara berurutan, mencetak jumlah baris tabel analitik, ringkasan listing per marketplace, serta riwayat snapshot katalog.

---

## 🦆 DuckLake dan Model Analitik

Katalog DuckLake yang digunakan adalah:

```text
lakehouse/shared_catalog.ducklake
```

DuckLake menggunakan `lakehouse/shared_catalog.ducklake` sebagai file katalog metadata dan `lakehouse/shared_catalog.ducklake.files/` sebagai direktori penyimpanan data fisik tabel, termasuk berkas Parquet. Pertahankan pasangan path ini agar katalog dapat menemukan data tabel yang dikelolanya.

### Empat query analitik di `sql/lake/`

| File | Tabel output | Fungsi |
|---|---|---|
| `10_dim_phone.sql` | `lake.analytics.dim_phone` | Master model HP dari `lake.gsmarena.clean_spek`, termasuk spesifikasi dan token nama untuk pemetaan listing. |
| `11_map_listing.sql` | `lake.analytics.map_listing` | Menggabungkan listing Tokopedia dan Shopee, lalu mencocokkan judul produk dengan nama model HP. Menyimpan informasi kecocokan dan ambiguitas. |
| `12_fact_price.sql` | `lake.analytics.fact_price` | Membentuk satu baris per listing yang berhasil dipetakan, beserta harga, rating, penjualan, penjual, dan penanda kualitas (`layak`, `pasti`). |
| `13_mart_banding_harga.sql` | `lake.analytics.banding_harga` | Menghitung jumlah listing, median harga, total terjual per marketplace, selisih harga, persentase selisih, dan penanda `cukup_data` per model. |

### Makna tabel analitik

- **`dim_phone`**: referensi model HP dan spesifikasinya.
- **`map_listing`**: hasil hubungan listing marketplace dengan `phone_id`.
- **`fact_price`**: detail listing harga yang berhasil dipetakan.
- **`banding_harga`**: ringkasan perbandingan harga Tokopedia dan Shopee pada tingkat model HP.

### Logika kualitas dan perbandingan

Di `fact_price`, `layak` dibentuk dari penanda harga wajar, bukan aksesori, dan URL pertama. `pasti` menunjukkan pemetaan yang tidak ambigu atau cocok dengan keyword pencarian. Mart perbandingan hanya mengagregasi baris yang memenuhi `layak AND pasti`.

Rumus selisih yang digunakan:

```text
Selisih (Rp) = median harga Shopee − median harga Tokopedia

Selisih (%) = 100 × (median Shopee − median Tokopedia)
                    / median Tokopedia
```

Nilai positif berarti median Shopee lebih tinggi; nilai negatif berarti median Shopee lebih rendah. `cukup_data` bernilai benar bila tersedia minimal tiga listing layak dan pasti pada masing-masing marketplace. Ini adalah ambang kecukupan data yang dipakai query, bukan bukti statistik bahwa perbandingan sudah mewakili seluruh pasar.

**Catatan arsitektur:** SQL lakehouse yang tersedia saat ini membangun empat tabel analitik di atas. README versi sebelumnya menyebut star schema dengan `fact_sales`, `dim_brand`, `dim_platform`, `dim_seller`, `dim_date`, serta mart sentimen. Tabel-tabel tersebut **tidak dibangun oleh file `sql/lake/10–13` yang ada dalam project saat ini**, sehingga tidak didokumentasikan sebagai tabel implementasi aktif.

---

## 📊 Dashboard Streamlit

File utama: `dashboard/dashboard.py`.

Dashboard membuka koneksi DuckLake untuk membaca data. Terdapat juga mode lokal yang membangun katalog sementara dan memanggil fungsi publikasi serta SQL lakehouse. Fungsi pemuatan data mengambil tabel analitik serta tabel komentar/penyebutan merek yang dibutuhkan untuk menampilkan grafik dan tabel.

### Tab yang tersedia

| Tab | Fokus analisis |
|---|---|
| **Ringkasan** | KPI model terpetakan, listing dianalisis, median harga, jumlah terjual terlapor, dan komentar YouTube bersih. |
| **Pasar & Harga** | Eksplorasi distribusi harga, segmen, merek, listing, dan indikator pasar. |
| **Shopee vs Tokopedia** | Perbandingan median harga, jumlah listing, selisih persentase, distribusi selisih, dan unduhan CSV. Tab ini memakai `banding_harga`. |
| **Spesifikasi vs Harga** | Eksplorasi hubungan atribut spesifikasi HP dengan harga. Analisisnya bersifat deskriptif/asosiatif, bukan bukti sebab-akibat. |
| **Suara Komentar** | Analisis teks komentar, frekuensi kata, dan penyebutan merek. Ini bukan klasifikasi sentimen positif/netral/negatif kecuali ada model/label tambahan yang belum terdapat di pipeline SQL saat ini. |
| **Data & Kualitas** | Informasi cakupan, pemetaan listing, penanda kualitas data, dan pemeriksaan data/snapshot yang tersedia. |

Dashboard memiliki filter sidebar, termasuk sumber data, merek, marketplace, rentang harga, dan jumlah minimum listing per model. Hasil visualisasi bergantung pada filter dan data yang lolos kriteria analisis.

### Menjalankan dashboard

Dari folder root project:

```powershell
python -m streamlit run dashboard/dashboard.py
```

Dashboard berjalan pada alamat lokal yang ditampilkan oleh Streamlit, umumnya `http://localhost:8501`.

---

## 🧪 Pengujian dan File Pendukung

- **`test_lake.py`**: menguji apakah katalog DuckLake dapat dibuka dan tabel analitik dapat dibaca.
- **`requirements.txt`**: daftar dependensi Python untuk DuckDB, Pandas, scraping, Streamlit, Plotly, dan Jupyter.
- **`README.md`**: dokumentasi arsitektur, pipeline, serta cara menjalankan project.
- **`notebook/01_scraping_gsmarena.ipynb`**, **`02_scraping_tokopedia.ipynb`**, dan **`03_scraping_shopee.ipynb`**: notebook pengambilan data.
- **`notebook/04_build_ducklake.ipynb`**: notebook pembangunan/eksplorasi DuckLake; untuk pipeline modular yang ada saat ini, entry point eksekusi tersedia di `SRC/`.
- **`*.duckdb.wal`**: file write-ahead log yang dapat muncul saat database DuckDB sedang digunakan. Jangan menghapusnya saat proses database aktif.

---

## ⚙️ Instalasi dan Menjalankan Project

Disarankan menggunakan virtual environment agar dependensi project tidak mengganggu paket Python lain.

### 1. Buat dan aktifkan virtual environment (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2. Pasang dependensi

```powershell
python -m pip install -r requirements.txt
```

DuckLake digunakan sebagai ekstensi DuckDB dan pada pemakaian pertama mungkin memerlukan akses internet untuk menginstal ekstensi.

### 3. Jalankan pipeline dari folder root

```powershell
python SRC/build_local.py
python SRC/publish.py
python SRC/build_lake.py
```

### 4. Jalankan dashboard

```powershell
python -m streamlit run dashboard/dashboard.py
```

Jika hanya mengubah query analitik, biasanya tahap yang perlu dijalankan ulang adalah `python SRC/build_lake.py`, asalkan tabel sumber sudah dipublikasikan. Jika data CSV berubah, jalankan ulang `build_local.py`, `publish.py`, lalu `build_lake.py`.

---

## ⚠️ Batasan dan Hal yang Perlu Diperhatikan

- Data marketplace adalah snapshot pada waktu scraping; harga, rating, dan jumlah terjual dapat berubah.
- Tidak semua listing berhasil dipetakan ke model HP. Kesalahan atau ambiguitas nama produk dapat memengaruhi hasil.
- Harga aksesori, harga tidak wajar, URL duplikat, dan pemetaan yang tidak meyakinkan ditandai/dikecualikan dari perbandingan sesuai aturan SQL.
- Listing untuk satu model bisa berbeda kondisi, varian RAM/storage, bundling, garansi, atau penjual; median harga tidak selalu membandingkan produk yang benar-benar identik.
- Jumlah terjual marketplace dapat berupa angka perkiraan dari label seperti `1rb+`.
- Data YouTube yang ada mendukung pembersihan komentar dan penghitungan penyebutan merek. Pipeline yang tersedia belum membuktikan sentimen dan belum menggabungkan skor sentimen dengan harga/penjualan.
- Jumlah baris harus dibaca dari hasil build terkini karena CSV dan database dapat berubah.
- Path katalog dan path data DuckLake harus konsisten. Jika katalog dipindahkan, validasi kembali akses tabel sebelum menjalankan dashboard.

---

## 🚧 Status Implementasi Berdasarkan Kode Saat Ini

### Sumber dan ETL

- [x] CSV tersedia untuk GSMArena, Tokopedia, Shopee, dan komentar YouTube.
- [x] SQL ingest, staging, clean, dan mart tersedia untuk keempat sumber.
- [x] Program build database lokal tersedia di `SRC/build_local.py`.
- [x] Program publikasi tabel sumber ke DuckLake tersedia di `SRC/publish.py`.
- [x] Program integrasi analitik tersedia di `SRC/build_lake.py`.

### Lakehouse dan analitik

- [x] `analytics.dim_phone`
- [x] `analytics.map_listing`
- [x] `analytics.fact_price`
- [x] `analytics.banding_harga`
- [ ] Model klasifikasi sentimen YouTube positif/netral/negatif
- [ ] Mart gabungan sentimen dengan harga/penjualan
- [ ] Star schema `fact_sales` dengan dimensi tanggal/platform/penjual/merek seperti yang disebut pada dokumentasi lama

### Dashboard

- [x] Ringkasan
- [x] Pasar & Harga
- [x] Shopee vs Tokopedia
- [x] Spesifikasi vs Harga
- [x] Suara Komentar
- [x] Data & Kualitas

Status `[x]` menunjukkan komponen/kode tersedia dalam project, bukan jaminan bahwa seluruh analisis bebas dari error atau semua hasil memiliki cakupan data yang besar.

---

## 🛠️ Teknologi

- **Python** — bahasa pemrograman pipeline dan dashboard.
- **DuckDB** — database analitik lokal dan mesin SQL.
- **DuckLake** — katalog lakehouse dan pengelolaan data tabel berbasis file Parquet.
- **SQL** — ingestion, standardisasi, cleaning, agregasi, pemetaan listing, dan pembangunan tabel analitik.
- **Pandas / NumPy** — pengolahan data dan perhitungan numerik di dashboard.
- **Requests / BeautifulSoup / lxml / Selenium** — scraping yang digunakan dalam notebook terkait.
- **Streamlit** — dashboard interaktif.
- **Plotly** — grafik interaktif.
- **Jupyter / ipykernel** — menjalankan notebook.

---

## 🎯 Output Project

Output aktif project saat ini adalah dashboard analitik yang menghubungkan spesifikasi HP GSMArena dengan listing marketplace yang berhasil dipetakan. Pengguna dapat menelusuri kualitas pemetaan, membandingkan median harga Shopee dan Tokopedia, mengeksplorasi hubungan spesifikasi dan harga, serta melihat analisis komentar/penyebutan merek YouTube.

Alur ringkasnya:

```text
Data sumber
  ↓
DuckDB lokal per sumber
  ↓
SQL ETL: raw → staging → clean → mart
  ↓
Publikasi ke DuckLake
  ↓
Integrasi: dim_phone → map_listing → fact_price → banding_harga
  ↓
Dashboard Streamlit
```

Dengan demikian, project ini bukan sekadar visualisasi, melainkan pipeline analitik multi-sumber. Dokumentasi ini membedakan fitur yang memang dibangun oleh kode saat ini dari ide pengembangan lanjutan seperti klasifikasi sentimen dan star schema yang lebih luas.
