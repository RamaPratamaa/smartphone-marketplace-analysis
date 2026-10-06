# 📱 Smartphone Data Warehouse — Spesifikasi, Harga Marketplace & Persepsi Publik

Project **PJBL Data Mining II** ini membangun sebuah **data warehouse (lakehouse) smartphone** yang mengintegrasikan data spesifikasi dari **GSMArena**, data harga & penjualan dari **Tokopedia** dan **Shopee**, serta (sebagai tahap lanjutan) sentimen komentar **YouTube**. Seluruh data disimpan di **DuckDB**, diintegrasikan ke **DuckLake** dengan *star schema*, lalu divisualisasikan melalui dashboard **Streamlit**.

> Analisis harga, penjualan, dan persepsi publik smartphone di marketplace Indonesia, dari proses scraping hingga dashboard interaktif.

---

# 🎯 Tujuan Project

Project ini bertujuan membangun pipeline **Data Ingestion → ETL → Data Warehouse/Lakehouse → Analytics → Dashboard** untuk menjawab pertanyaan seperti:

- Berapa selisih harga HP yang sama antara Tokopedia dan Shopee?
- Marketplace mana yang lebih murah untuk HP tertentu?
- Bagaimana harga, rating, dan jumlah terjual berbeda antar brand?
- Bagaimana hubungan spesifikasi (chipset, RAM, storage, baterai) dengan harga?
- Apakah HP dengan sentimen positif di YouTube juga memiliki performa penjualan yang lebih baik di marketplace?
- HP mana yang harganya tinggi tetapi sentimen negatifnya juga tinggi?

**Pertanyaan riset utama:**
> *Apakah brand/HP yang mendapat sentimen positif di YouTube juga memiliki harga dan penjualan yang lebih baik di marketplace Indonesia?*

---

# 👥 Anggota Tim

| Nama | Tugas Utama |
|---|---|
| Firqi | [isi tugas] |
| Yudha | [isi tugas] |
| Rama | [isi tugas] |

> Mata kuliah: **Data Mining II** — Semester 7

---

# 📦 Dataset

Project menggunakan tiga sumber data utama yang di-*scrape* sendiri, ditambah satu sumber sentimen.

## 1. 📘 GSMArena — Spesifikasi HP

**Sumber:** [gsmarena.com](https://www.gsmarena.com)
**Metode:** `requests` + `BeautifulSoup`
**File mentah:** `data/raw_dataset_gsmarena.csv` · `database/gsmarena.duckdb`

Berisi spesifikasi HP rilis **2025 ke atas** dari 10 brand yang populer di Indonesia:

```text
Samsung · Xiaomi · Oppo · Vivo · Realme · Infinix · Tecno · itel · Apple · Huawei
```

| Kolom mentah | Contoh |
|---|---|
| `brand`, `phone_name` | Samsung, Samsung Galaxy A17 |
| `chipset_raw` | `Exynos 1480 (4 nm)` |
| `internalmemory_raw` | `128GB 8GB RAM` |
| `battery_raw`, `released_raw`, `release_year` | — |
| `gsmarena_url`, `scraped_at` | — |

Granularitas: `1 baris = 1 model HP`

Data mentah: **282 HP** → setelah dibersihkan menjadi **270 HP** siap pakai (rilis ≥ 2025). Daftar nama HP ini juga menjadi **daftar keyword pencarian** untuk Tokopedia dan Shopee.

---

## 2. 🛒 Tokopedia — Harga & Penjualan

**Sumber:** [tokopedia.com](https://www.tokopedia.com)
**Metode:** Selenium (tersambung ke Chrome remote debugging) + `BeautifulSoup`
**File mentah:** `data/raw_dataset_tokopedia.csv` · `database/tokopedia.duckdb`

Data mentah: **1.451 listing** dari ±182 keyword HP (scraping 1–3 Oktober 2026).

---

## 3. 🛍️ Shopee — Harga & Penjualan

**Sumber:** [shopee.co.id](https://shopee.co.id)
**Metode:** Selenium + `BeautifulSoup` (mode semi-manual karena Shopee memblokir akses otomatis)
**File mentah:** `data/raw_dataset_shopee.csv` · `database/shopee.duckdb`

Data mentah: **606 listing** dari ±167 keyword HP (scraping 3–4 Oktober 2026).

Struktur kolom mentah Tokopedia & Shopee sama:

| Kolom | Keterangan |
|---|---|
| `keyword` | Nama HP yang dicari (dari GSMArena) |
| `product_name`, `product_url` | Judul & link listing |
| `price_discount_raw`, `price_original_raw` | Harga setelah/sebelum diskon (masih teks, mis. `Rp1.999.000`) |
| `discount_label_raw` | Label diskon |
| `rating_raw`, `sold_raw` | Rating & jumlah terjual (mis. `1,2rb+ terjual`) |
| `seller_name`, `seller_location` | Info penjual |
| `scraped_at` | Waktu scraping |

Granularitas: `1 baris = 1 listing produk di 1 platform`

---

## 4. 🎥 YouTube — Komentar Review

**Sumber:** Komentar pada channel review gadget Indonesia
**File:** `database/youtube.duckdb` 

Data ini dipakai untuk menghitung **sentimen per HP** (positif / netral / negatif). Pipeline akan otomatis menyertakan data YouTube begitu `youtube.duckdb` dengan tabel `fact_youtube_sentiment` tersedia. Selama belum ada, bagian sentimen di dashboard ditampilkan sebagai *"belum tersedia"*.

---

# 🔗 Integrasi Sumber Data

| Sumber | Peran | Granularitas | Kunci Integrasi |
|---|---|---|---|
| GSMArena | Dimensi HP (spesifikasi) | 1 model HP | `phone_name` baku |
| Tokopedia | Fakta harga & penjualan | 1 listing | dicocokkan ke `phone_name` |
| Shopee | Fakta harga & penjualan | 1 listing | dicocokkan ke `phone_name` |
| YouTube *(opsional)* | Fakta sentimen | 1 komentar | `phone_id` |

Judul listing marketplace tidak seragam (mis. `"iPhone 16 128gb NEW BARU SEGEL"`), sehingga setiap listing **dicocokkan ke nama HP baku GSMArena** menggunakan normalisasi nama, pencocokan varian (`Pro`, `Plus`, `Ultra`, `Max`, dll.), dan pencocokan RAM/storage dari judul.

> Karena metodologi dan isi listing tiap platform berbeda, selisih harga disebut sebagai **price gap** antar platform, bukan otomatis sebagai kelebihan/kekurangan suatu marketplace.

---

# 🏗️ Arsitektur Data Warehousing

Project mengikuti arsitektur **medallion** (bronze → gold):

```text
                 DATA SOURCES
                      │
     ┌────────────┬───┴────────┬────────────┐
     ▼            ▼            ▼            ▼
 GSMArena     Tokopedia      Shopee      YouTube*
(requests)    (Selenium)    (Selenium)   (opsional)
     │            │            │            │
     ▼            ▼            ▼            ▼
gsmarena      tokopedia      shopee      youtube
 .duckdb       .duckdb       .duckdb     .duckdb
     │            │            │            │
     └────────────┴─────┬──────┴────────────┘
                        │      BRONZE (data mentah per sumber)
                        ▼
              ETL / ELT (04_build_ducklake)
       bersihkan → cocokkan nama → seimbangkan jumlah data
                        │
                        ▼
                    DUCKLAKE        GOLD (star schema)
              lakehouse.ducklake
                  + file Parquet
                        │
                        ▼
                ANALYTICS MART
                        │
                        ▼
                STREAMLIT DASHBOARD
```

---

# 🗄️ Bronze Layer — Local DuckDB

Setiap sumber memiliki database DuckDB sendiri yang berfungsi sebagai **raw/staging layer**. Data disimpan **apa adanya** dari sumber (kolom `*_raw` masih berupa teks), sehingga selalu dapat ditelusuri.

| Database | Tabel | Isi |
|---|---|---|
| `gsmarena.duckdb` | `phone_specs` | Spesifikasi mentah per HP |
| `tokopedia.duckdb` | `listings`, `search_progress` | Listing mentah & checkpoint keyword |
| `shopee.duckdb` | `listings`, `search_progress` | Listing mentah & checkpoint keyword |

**Fitur penting scraping:**

- **Checkpoint di dalam DuckDB** — scraping dapat dihentikan dan dilanjutkan kapan saja; HP/keyword yang sudah tersimpan otomatis dilewati.
- **Penyaringan aksesoris** — listing case, charger, tempered glass, dsb. dibuang sejak bronze.
- **Rate-limit aware** — jeda acak antar request dan berhenti otomatis jika terdeteksi blokir.
- **Round-robin keyword** — keyword dipilih bergantian antar brand supaya semua brand terwakili.
- **Ekspor CSV** — `data/raw_dataset_*.csv` selalu dibuat ulang dari isi tabel DuckDB (untuk lampiran laporan, bukan sumber data utama).

---

# 🦆 Gold Layer — DuckLake & Star Schema

Data dari seluruh bronze di-`ATTACH` (read-only), dibersihkan, lalu ditulis ke satu **DuckLake**:

- `lakehouse.ducklake` — catalog/metadata
- `files/` — file Parquet (data fisik)

## Star Schema

```text
                 dim_brand
                     │
                     ▼
dim_date ──►  fact_sales  ◄── dim_phone
                 ▲   ▲
                 │   │
         dim_platform  dim_seller
```

| Tabel | Jenis | Isi |
|---|---|---|
| `dim_brand` | Dimensi | 10 brand |
| `dim_phone` | Dimensi | 270 HP + chipset, RAM, storage, baterai, tahun rilis |
| `dim_platform` | Dimensi | Tokopedia, Shopee |
| `dim_seller` | Dimensi | Penjual & lokasi |
| `dim_date` | Dimensi | Tanggal scraping (hari, bulan, kuartal, tahun) |
| `fact_sales` | Fakta | Listing bersih: harga asli, harga diskon, % diskon, rating, jumlah terjual |
| `mart_price_stats` | Mart | Median/rata-rata/min/maks harga per HP per platform |
| `mart_price_comparison` | Mart | Selisih harga Tokopedia vs Shopee per HP (Rp & %) |
| `mart_sentiment_summary` | Mart *(opsional)* | % positif/netral/negatif per HP |
| `mart_sentiment_vs_price` | Mart *(opsional)* | Gabungan sentimen dan harga per HP |

---

# 🔄 ETL / ELT Process

## 1. Extract

Scraping tiga sumber ke bronze DuckDB (notebook `01`–`03`).

## 2. Transform

Dilakukan di notebook `04_build_ducklake.ipynb`:

**Spesifikasi HP (GSMArena)**
- memisahkan nama chipset dari detail proses (mis. `Exynos 1480 (4 nm)` → `Exynos 1480`),
- mengidentifikasi brand chipset (Snapdragon, Exynos, Dimensity, Helio, Tensor, dst.),
- parsing RAM, storage, dan baterai dari teks menjadi **angka** (GB / mAh),
- membuang HP batal rilis/rumor dan memastikan jendela tahun `MIN_YEAR = 2025`.

**Penjualan (Tokopedia & Shopee)**
- mengubah harga `"Rp1.999.000"` → angka integer,
- mengubah jumlah terjual `"1,2rb+ terjual"` → angka,
- parsing rating dan persentase diskon,
- membuang HP bekas (`second`, `bekas`, `preloved`, `refurbish`, dst.),
- membuang harga di bawah `Rp300.000` (bukan HP),
- menghapus listing duplikat.

**Pencocokan & penyeimbangan**
- memetakan judul listing ke nama HP baku GSMArena,
- membuang listing yang tidak cocok,
- menyamakan jumlah listing per HP antar platform (`LISTINGS_PER_PHONE = 10`, minimal 5) agar perbandingan adil.

## 3. Load

Hasil ditulis ke DuckLake menggunakan `CREATE OR REPLACE TABLE lake.<nama_tabel>`, kemudian divalidasi:

- foreign key `phone_id`, `platform_id`, `seller_id` tidak boleh orphan,
- ukuran folder lakehouse dicek terhadap batas GitHub (peringatan di 50 MB, batas keras 100 MB/file).

---

# 📊 Ringkasan Volume Data

| Tahap | GSMArena | Tokopedia | Shopee |
|---|---:|---:|---:|
| Mentah (bronze) | 282 HP | 1.451 listing | 606 listing |
| Setelah cleaning | 270 HP | 951 listing | 307 listing |
| Gold (dicocokkan & diseimbangkan) | 270 HP di `dim_phone` | 45 listing | 45 listing |

Pada build terakhir, **8 HP** berhasil dibandingkan harganya di kedua platform (**90 listing** di `fact_sales`). Angka ini akan bertambah seiring scraping dilanjutkan dan notebook `04` dijalankan ulang.

---

# 📈 Arah Analisis

## 1. Perbandingan Harga Antar Platform

```text
Selisih (Rp)  = Harga median Shopee − Harga median Tokopedia

Selisih (%)   =  (Shopee − Tokopedia)
                 ───────────────────── × 100%
                       Tokopedia
```

Output: tabel dan grafik batang harga per HP, serta kolom `lebih_murah` (Shopee / Tokopedia / Sama).

## 2. Statistik Harga per HP

Median, rata-rata, minimum, maksimum, rata-rata rating, dan total terjual per HP per platform. **Median** dipakai sebagai indikator utama agar tidak terlalu dipengaruhi listing berharga ekstrem.

## 3. Analisis Brand & Spesifikasi

Perbandingan harga, rating, dan penjualan antar brand; serta hubungan chipset, RAM, storage, dan baterai terhadap harga.

## 4. Sentimen vs Harga *(tahap lanjutan)*

Menghubungkan persepsi publik di YouTube dengan harga di marketplace. Pendekatan **weighted sentiment** dipakai untuk menangani ketimpangan jumlah komentar antar HP:

```text
weighted_sentiment = sentiment_score_avg × log(1 + jumlah_komentar)
```

Dashboard memberi label `indikasi_branding` berdasarkan aturan sederhana (ambang rasio 1,5×). Ini **bukan** kesimpulan statistik yang ketat.

---

# 🖥️ Dashboard Streamlit

File: `dashboard/dashboard.py`

Dashboard membaca langsung dari **DuckLake** (`ATTACH 'ducklake:...' (READ_ONLY)`), tanpa menyentuh file bronze.

## Filter (Sidebar)

```text
Brand · Tahun Rilis · Rentang Harga
```

## Bagian Dashboard

| Bagian | Isi |
|---|---|
| **Ringkasan** | Jumlah HP di database, jumlah HP yang dibandingkan, total listing, rata-rata selisih Shopee vs Tokopedia |
| **💰 Perbandingan Harga** | Tabel selisih harga + grafik batang 20 HP dengan harga tertinggi |
| **💬 Sentimen YouTube** | Scatter harga vs % komentar negatif, tabel ringkasan, indikasi branding *(muncul jika data tersedia)* |
| **🔎 Detail per HP** | Chipset, RAM, storage, baterai, harga di tiap platform, dan sentimen |

Bagian yang datanya belum tersedia akan menampilkan pesan informatif, bukan error.

---

# 📁 Struktur Repository

```text
PJBL/
│
├── data/                           # Salinan CSV data mentah (untuk laporan)
│   ├── raw_dataset_gsmarena.csv
│   ├── raw_dataset_tokopedia.csv
│   └── raw_dataset_shopee.csv
│
├── database/                       # Bronze layer (DuckDB per sumber)
│   ├── gsmarena.duckdb
│   ├── tokopedia.duckdb
│   └── shopee.duckdb
│
├── lakehouse/                      # Gold layer (DuckLake)
│   ├── lakehouse.ducklake          # Catalog / metadata
│   └── files/                      # File Parquet milik DuckLake
│
├── notebook/
│   ├── 01_scraping_gsmarena.ipynb  # Bronze: spesifikasi HP
│   ├── 02_scraping_tokopedia.ipynb # Bronze: harga & penjualan Tokopedia
│   ├── 03_scraping_shopee.ipynb    # Bronze: harga & penjualan Shopee
│   └── 04_build_ducklake.ipynb     # Gold: cleaning, matching, star schema
│
├── dashboard/
│   └── dashboard.py                # Dashboard Streamlit
│
├── README.md
└── requirements.txt
```

---

# ⚙️ Cara Install & Menjalankan

## 1. Clone Repository

```bash
git clone https://github.com/[username]/[nama-repo].git
cd [nama-repo]
```

## 2. Buat Virtual Environment (Direkomendasikan)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

## 3. Install Dependensi

```bash
pip install -r requirements.txt
```

Notebook scraping memasang library tambahan sendiri lewat `%pip install` (`requests`, `beautifulsoup4`, `lxml`, `selenium`).

## 4. Jalankan Notebook Sesuai Urutan

Jalankan dari **folder root repo** supaya path relatif benar.

| Urutan | Notebook | Tujuan | Output |
|---|---|---|---|
| 1 | `01_scraping_gsmarena.ipynb` | Scraping spesifikasi HP | `gsmarena.duckdb` |
| 2 | `02_scraping_tokopedia.ipynb` | Scraping listing Tokopedia | `tokopedia.duckdb` |
| 3 | `03_scraping_shopee.ipynb` | Scraping listing Shopee | `shopee.duckdb` |
| 4 | `04_build_ducklake.ipynb` | Cleaning, matching, star schema | `lakehouse.ducklake` |

> Notebook 02 dan 03 **membutuhkan** `gsmarena.duckdb` terisi lebih dulu (sebagai daftar keyword). Notebook 03 secara opsional memprioritaskan keyword dari `tokopedia.duckdb`.

### Persiapan Scraping Tokopedia & Shopee

Selenium tersambung ke **Chrome yang dibuka manual** dengan remote debugging (bukan membuka browser baru), supaya captcha/login bisa diselesaikan sendiri:

```bash
# Windows (Command Prompt)
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
```

Lalu buka `tokopedia.com` / `shopee.co.id` (Shopee: login terlebih dahulu) dan lakukan satu pencarian manual sebelum menjalankan notebook.

## 5. Jalankan Dashboard

```bash
streamlit run dashboard/dashboard.py
```

Buka di browser: `http://localhost:8501`

---

# 🛠️ Tools dan Teknologi

- **Python**
- **DuckDB** — database bronze per sumber & SQL processing
- **DuckLake** — lakehouse (catalog + Parquet)
- **Pandas** — cleaning dan transformasi
- **Requests + BeautifulSoup (lxml)** — scraping GSMArena
- **Selenium** — scraping Tokopedia & Shopee
- **Streamlit** — dashboard interaktif
- **Plotly** — visualisasi interaktif
- **Git / GitHub** — version control

Dependensi dashboard (`requirements.txt`): `streamlit`, `duckdb`, `pandas`, `plotly`.

---

# 🧩 Penerapan Data Warehousing

Project ini menerapkan konsep-konsep utama data warehousing secara langsung, mulai dari ingestion hingga penyajian ke dashboard.

| Konsep | Penerapan di Project Ini |
|---|---|
| **Multi-source integration** | Tiga sumber heterogen (GSMArena, Tokopedia, Shopee) + YouTube opsional, diintegrasikan ke satu model data terpadu |
| **Arsitektur medallion** | **Bronze** = data mentah per sumber (`*.duckdb`), **Gold** = data bersih & terintegrasi (DuckLake). Bronze tidak diubah, sehingga selalu dapat ditelusuri |
| **Staging layer** | Satu database DuckDB per sumber berfungsi sebagai staging sebelum transformasi |
| **ETL / ELT** | Extract lewat scraping (notebook 01–03), Transform & Load lewat SQL + Pandas (notebook 04) |
| **Dimensional modeling** | *Star schema* dengan 1 tabel fakta (`fact_sales`) dan 5 tabel dimensi (`dim_brand`, `dim_phone`, `dim_platform`, `dim_seller`, `dim_date`) |
| **Grain tabel fakta** | 1 baris = 1 listing produk di 1 platform pada 1 tanggal scraping |
| **Surrogate key** | Setiap dimensi memiliki ID buatan (`brand_id`, `phone_id`, `platform_id`, `seller_id`, `date_id`) sebagai penghubung ke tabel fakta |
| **Data cleaning & standardisasi** | Harga teks → angka, `"1,2rb+ terjual"` → angka, RAM/storage/baterai → numerik, nama chipset disederhanakan |
| **Data quality & validasi** | Pembuangan aksesoris, HP bekas, harga < Rp300.000, duplikat, dan listing yang tidak cocok; cek foreign key sebelum data dianggap valid |
| **Entity matching** | Judul listing marketplace dipetakan ke nama HP baku GSMArena (normalisasi nama, varian, RAM/storage) |
| **Data mart** | Tabel analitik siap pakai: `mart_price_stats`, `mart_price_comparison`, dan mart sentimen *(opsional)* |
| **Lakehouse** | DuckLake: metadata di `lakehouse.ducklake`, data fisik berupa file Parquet di `files/` |
| **Checkpointing & idempotent load** | Scraping dapat dilanjutkan tanpa duplikasi; `CREATE OR REPLACE TABLE` membuat build ulang gold aman dijalankan berkali-kali |
| **Read-only serving layer** | Dashboard Streamlit membaca gold lewat `ATTACH ... (READ_ONLY)`, tanpa menyentuh bronze |
| **Lineage & reproducibility** | Alur data terdokumentasi lewat notebook berurutan; kolom `scraped_at` dan `dim_date` mencatat waktu pengambilan data |

---

# ⚠️ Catatan Data & Keterbatasan

- Data bersifat **snapshot** pada tanggal scraping; harga marketplace dapat berubah kapan saja.
- Hanya sebagian kecil HP yang ditemukan di **kedua** platform, sehingga perbandingan harga baru mencakup **8 HP** pada build terakhir.
- Listing marketplace dapat berisi varian, bundling, atau penjual dengan kondisi berbeda sehingga harga tidak selalu *apple-to-apple*.
- Beberapa HP dari GSMArena belum dijual resmi di Indonesia (mis. varian China/India) sehingga tidak ditemukan di marketplace.
- Shopee memblokir akses otomatis; sebagian data dikumpulkan secara semi-manual.
- Jumlah terjual di marketplace berupa teks pembulatan (mis. `1rb+`), sehingga hanya perkiraan.
- Label `indikasi_branding` adalah aturan sederhana, bukan uji statistik.
- Scraping hanya untuk keperluan akademik; hormati ketentuan layanan masing-masing situs.

---

# 🚧 Status Project

### Data

- [x] Scraping spesifikasi HP (GSMArena)
- [x] Scraping listing Tokopedia
- [x] Scraping listing Shopee
- [ ] Scraping & sentimen komentar YouTube
- [ ] Menambah jumlah HP yang tercocokkan di kedua platform

### Data Warehousing

- [x] Bronze layer (`gsmarena`, `tokopedia`, `shopee` `.duckdb`)
- [x] Cleaning & transformasi
- [x] Pencocokan nama HP antar sumber
- [x] Star schema di DuckLake
- [x] Mart perbandingan harga
- [ ] Mart sentimen (menunggu `youtube.duckdb`)

### Analytics

- [x] Perbandingan harga Tokopedia vs Shopee
- [x] Statistik harga per HP
- [ ] Analisis brand & spesifikasi vs harga
- [ ] Korelasi sentimen vs penjualan
- [ ] Gap analysis (overrated vs underrated)

### Dashboard

- [x] Filter brand, tahun rilis, rentang harga
- [x] Perbandingan harga
- [x] Detail per HP
- [ ] Bagian sentimen YouTube (kode siap, menunggu data)
- [ ] Deployment (Streamlit Community Cloud)

---

# 📝 Catatan Teknis

- **File `.duckdb` ikut di-commit ke GitHub.** Batas keras GitHub adalah 100 MB/file. Notebook mencetak ukuran file setelah selesai; jika mendekati batas, pertimbangkan Git LFS.
- File `*.duckdb.wal` adalah file sementara DuckDB dan umumnya tidak perlu di-commit (tambahkan ke `.gitignore`).
- Jangan membuka satu file `.duckdb` di dua notebook sekaligus karena DuckDB mengunci file saat digunakan.
- Jalankan ulang `04_build_ducklake.ipynb` setiap ada data baru di bronze; `CREATE OR REPLACE TABLE` akan menimpa isi lama.
- Ekstensi DuckLake diunduh otomatis lewat `INSTALL ducklake` (butuh internet pada pemakaian pertama).

---

# 🎯 Expected Output

Output akhir project berupa **data warehouse dan dashboard analitik smartphone** yang memungkinkan pengguna mengeksplorasi:

```text
BRAND
  ↓
MODEL HP
  ↓
SPESIFIKASI
  ↓
HARGA TIAP PLATFORM
  ↓
SENTIMEN PUBLIK
```

dan menghasilkan informasi mengenai:

```text
Harga · Selisih antar platform · Rating · Penjualan · Spesifikasi · Sentimen
```

Dengan demikian, project ini tidak hanya berfungsi sebagai visualisasi data, tetapi sebagai implementasi proses **Web Scraping → Bronze (DuckDB) → ETL → Gold (DuckLake, Star Schema) → Analytics → Interactive Dashboard (Streamlit)**.
