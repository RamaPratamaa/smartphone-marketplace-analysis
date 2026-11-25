"""
Dashboard Analisis Pasar Smartphone Indonesia
(Shopee + Tokopedia + GSMArena + Komentar YouTube + Sebaran Wilayah)
"""
import contextlib
import html
import os
import re
import sys
import traceback
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "SRC"))
def _find_lake_dir() -> Path:
    """Mencari folder katalog DuckLake secara otomatis di berbagai struktur folder proyek."""
    candidates = [
        ROOT / "Proyek_DuckDB" / "DuckLake",
        ROOT / "Proyek_DuckDB" / "lakehouse",
        ROOT / "DuckLake",
        ROOT / "lakehouse",
    ]
    for path in candidates:
        if (path / "shared_catalog.ducklake").exists():
            return path
    return ROOT / "Proyek_DuckDB" / "DuckLake"


_lake_dir = _find_lake_dir()
LAKE_CATALOG = (_lake_dir / "shared_catalog.ducklake").as_posix()
_data_dir = (
    _lake_dir / "lakehouse_storage"
    if (_lake_dir / "lakehouse_storage").exists()
    else _lake_dir / "shared_catalog.ducklake.files"
)
LAKE_DATA = _data_dir.as_posix() + "/"

# Palet warna korporat (ramah tema terang maupun gelap)
NAVY, ACCENT, BLUE, SLATE = "#0F2D52", "#0E7C86", "#3E6FB0", "#64748B"
C_TOKPED, C_SHOPEE = "#16a34a", "#f97316"
COLORWAY = [
    "#3E6FB0", "#0E7C86", "#8CA6CF", "#D69E2E", "#7A869A",
    "#C2410C", "#5B8E7D", "#7C6BB5", "#475569", "#B4477A",
]
FONT = "Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
SEG_LABELS = [
    "Murah (< 2 jt)",
    "Menengah Bawah (2–4 jt)",
    "Menengah (4–7 jt)",
    "Menengah Atas (7–12 jt)",
    "Flagship (> 12 jt)",
]
SEG_BINS = [0, 2e6, 4e6, 7e6, 12e6, np.inf]

st.set_page_config(page_title="Dashboard Pasar HP Indonesia", layout="wide")

_axis = dict(
    gridcolor="rgba(128,128,128,0.18)",
    linecolor="rgba(128,128,128,0.45)",
    zerolinecolor="rgba(128,128,128,0.3)",
    ticks="outside",
    tickcolor="rgba(128,128,128,0.45)",
)
pio.templates["corp"] = go.layout.Template(
    layout=go.Layout(font=dict(family=FONT, size=12), colorway=COLORWAY, xaxis=_axis, yaxis=_axis)
)
pio.templates.default = "plotly_white+corp"

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {--navy:#0F2D52; --accent:#0E7C86; --line: rgba(128,128,128,.30); --soft: rgba(128,128,128,.08);}
html, body, .stApp, h1, h2, h3, h4, h5, h6, p, label, button, input, textarea, li {
    font-family: Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;}
#MainMenu, footer, .stDeployButton, [data-testid="stAppDeployButton"], [data-testid="stDecoration"] {display: none !important;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1360px;}

/* Header */
.topbar {background: var(--navy); color: #fff; padding: 1.5rem 2rem 1.4rem; border-radius: 8px;
         margin-bottom: 1.2rem; border-bottom: 4px solid var(--accent);}
.topbar .eyebrow {font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
                  color: #9FB6D3; font-weight: 600;}
.topbar h1 {margin: .25rem 0 .3rem; padding: 0; font-size: 1.7rem; font-weight: 700; color: #fff;
            letter-spacing: -.01em;}
.topbar p {margin: 0; color: #C9D6E8; font-size: .94rem;}

/* Tab Navigasi */
.stTabs [data-baseweb="tab-list"] {gap: 1.5rem; border-bottom: 1px solid var(--line);}
.stTabs [data-baseweb="tab"] {height: 3rem; padding: 0 .2rem; background: transparent;}
.stTabs [data-baseweb="tab"] p {font-weight: 600; font-size: .95rem; opacity: .7;}
.stTabs [aria-selected="true"] p {opacity: 1; color: var(--accent);}
.stTabs [data-baseweb="tab-highlight"] {background-color: var(--accent) !important; height: 3px;}
.stTabs [role="tablist"] .react-aria-SelectionIndicator {background-color: var(--accent) !important;}
span[data-baseweb="tag"], span[data-tag] {background-color: var(--accent) !important;}
.stTabs [data-baseweb="tab-border"] {background-color: transparent;}

/* Judul Bagian */
h4, h5 {font-weight: 700; letter-spacing: -.005em; color: inherit;}
h4 {font-size: 1.18rem; margin-top: .5rem;}
h5 {font-size: 1.02rem; margin-top: .4rem;}

/* Kartu KPI */
.kpi {background: var(--soft); border: 1px solid var(--line); border-top: 3px solid var(--accent);
      border-radius: 8px; padding: .95rem 1.1rem; min-height: 7.5rem;}
.kpi .l {font-size: .72rem; opacity: .75; text-transform: uppercase; letter-spacing: .06em; font-weight: 600;}
.kpi .v {font-size: 1.45rem; font-weight: 700; line-height: 1.35; margin: .15rem 0;}
.kpi .s {font-size: .78rem; opacity: .7;}

/* Kotak Kesimpulan & Catatan */
.insight {border-left: 4px solid var(--accent); background: rgba(14,124,134,.10); padding: .8rem 1.1rem;
          border-radius: 0 8px 8px 0; margin: .45rem 0; font-size: .94rem; line-height: 1.5;}
.warn {border-left: 4px solid #D69E2E; background: rgba(214,158,46,.12); padding: .75rem 1.1rem;
       border-radius: 0 8px 8px 0; margin: .5rem 0; font-size: .88rem; line-height: 1.45;}

/* Sidebar */
[data-testid="stSidebar"] {border-right: 1px solid var(--line);}
[data-testid="stSidebar"] h3 {font-size: .78rem; text-transform: uppercase; letter-spacing: .1em;
                              opacity: .75; font-weight: 700;}

/* Galeri HP */
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 8px; border-color: var(--line);}
[data-testid="stImage"] {display: flex; justify-content: center;}
[data-testid="stImage"] img {background: #fff; border-radius: 4px;}
.noimg {width: 130px; height: 173px; margin: 0 auto; background: var(--soft); border: 1px dashed var(--line);
        border-radius: 4px; display: flex; align-items: center; justify-content: center;
        opacity: .75; font-size: .72rem; text-align: center;}
.phone-name {font-size: .85rem; font-weight: 600; line-height: 1.25; min-height: 2.6em;
             text-align: center; margin-top: .35rem;}
.phone-price {font-size: .8rem; font-weight: 600; color: var(--accent); text-align: center; margin-bottom: .15rem;}
.phone-sold {font-size: .72rem; opacity: .65; text-align: center; margin-bottom: .45rem;}

/* Tombol & Metrik */
.stButton > button, .stDownloadButton > button {border-radius: 6px; font-weight: 600; font-size: .82rem;}
.stButton > button:hover, .stDownloadButton > button:hover {border-color: var(--accent); color: var(--accent);}
[data-testid="stMetric"] {background: var(--soft); border: 1px solid var(--line); border-radius: 8px;
                          padding: .65rem .85rem;}
[data-testid="stMetricLabel"] p {font-size: .74rem; opacity: .75; text-transform: uppercase; letter-spacing: .04em;}
[data-testid="stMetricValue"] {font-size: 1.25rem;}

/* Footer */
.footer {margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--line);
         opacity: .65; font-size: .8rem; text-align: center;}
</style>
""",
    unsafe_allow_html=True,
)

if (st.get_option("theme.primaryColor") or "").lower() != ACCENT.lower():
    st.markdown(
        "<style>[data-testid='stSlider'] {filter: hue-rotate(190deg) saturate(.85) brightness(.9);}</style>",
        unsafe_allow_html=True,
    )


# ============================ HELPER TAMPILAN ============================
def rp(x) -> str:
    """Format rupiah ringkas agar mudah dibaca: Rp 4,50 jt / Rp 850 rb."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    if abs(x) >= 1e6:
        return f"Rp {x / 1e6:,.2f} jt".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Rp {x / 1e3:,.0f} rb".replace(",", ".")


def num(x) -> str:
    return f"{x:,.0f}".replace(",", ".")


def kpi(col, label, value, sub=""):
    col.markdown(
        f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>'
        f'<div class="s">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def _html(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def insight(text: str):
    st.markdown(f'<div class="insight">{_html(text)}</div>', unsafe_allow_html=True)


def warn(text: str):
    st.markdown(f'<div class="warn">{_html(text)}</div>', unsafe_allow_html=True)


def style(fig, h=400):
    ada_judul = bool(fig.layout.title.text)
    ada_legenda = fig.layout.showlegend is not False and sum(
        1 for tr in fig.data if getattr(tr, "showlegend", None) is not False and getattr(tr, "name", None)
    ) >= 2
    top = (38 if ada_judul else 12) + (54 if ada_legenda else 0)
    fig.update_layout(
        height=h,
        margin=dict(l=10, r=15, t=top, b=10),
        title=dict(x=0, xanchor="left", y=0.99, yanchor="top", yref="container",
                   font=dict(size=15, family=FONT)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    title_text="", font=dict(size=11)),
    )
    return fig


@contextlib.contextmanager
def guard():
    try:
        yield
    except st.errors.StreamlitAPIException:
        raise
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR PADA DASHBOARD")
        traceback.print_exc()
        print("=" * 70 + "\n")
        st.error(f"Bagian ini gagal ditampilkan: {type(e).__name__}: {e}")


def show(fig, h=400):
    st.plotly_chart(style(fig, h), use_container_width=True)


def kategori_worth_it(skor: float) -> str:
    """Mengubah selisih skor spek & harga menjadi kategori awam yang mudah dipahami."""
    if skor >= 25:
        return "Sangat Worth-It (Spek Unggul)"
    if skor >= 5:
        return "Worth-It (Layak Beli)"
    if skor >= -15:
        return "Sesuai Harga Pasaran"
    return "Kelas Premium / Flagship"


# ============================ GALERI HP & POP-UP DETAIL ============================
def _find_img_dir() -> Path:
    for p in [
        ROOT / "data" / "phone_images",
        ROOT / "DataRaw" / "phone_images",
        ROOT.parent / "data" / "phone_images",
    ]:
        if p.exists():
            return p
    return ROOT / "data" / "phone_images"


IMG_DIR = _find_img_dir()


def phone_img(phone_id):
    f = IMG_DIR / f"{phone_id}.jpg"
    return str(f) if f.exists() else None


@st.dialog("Detail Spesifikasi & Harga HP", width="large")
def phone_popup(row, harga_mkt):
    c1, c2 = st.columns([1, 2])
    with c1:
        img = phone_img(row["phone_id"])
        if img:
            st.image(img, width=220)
            st.caption("Foto referensi: GSMArena")
        else:
            st.info("Foto belum tersedia untuk model ini.")
    with c2:
        st.markdown(f"### {row['phone_name']}")
        st.caption(f"Merek: **{row['brand']}**")
        k = st.columns(3)
        k[0].metric("Harga Pasaran (Rata-rata Tengah)", rp(row["harga_median"]))
        k[1].metric("Estimasi Unit Terjual", f"{num(row['terjual'])} unit")
        k[2].metric("Jumlah Toko", f"{num(row['listing'])} toko")

        if len(harga_mkt):
            st.markdown("**Perbandingan Harga di Toko Online**")
            for mkt, hrg in harga_mkt.items():
                st.write(f"- **{str(mkt).title()}**: {rp(hrg)}")

        spek = []
        if pd.notna(row["ram"]):
            spek.append(f"RAM hingga **{row['ram']:.0f} GB**")
        if pd.notna(row["storage"]):
            spek.append(f"Memori hingga **{row['storage']:.0f} GB**")
        if pd.notna(row["baterai"]):
            spek.append(f"Baterai **{row['baterai']:.0f} mAh**")
        if pd.notna(row["tahun"]):
            spek.append(f"Tahun rilis **{row['tahun']:.0f}**")
        if spek:
            st.markdown("**Spesifikasi Utama**")
            st.write(" • ".join(spek))


# ============================ KONEKSI & DATA DUCKDB ============================
@st.cache_resource
def get_con():
    con = duckdb.connect()
    con.execute("INSTALL ducklake; LOAD ducklake;")
    con.execute(
        f"ATTACH 'ducklake:{LAKE_CATALOG}' AS lake "
        f"(DATA_PATH '{LAKE_DATA}', OVERRIDE_DATA_PATH TRUE, READ_ONLY)"
    )
    return con


@st.cache_data(show_spinner="Menyiapkan data pasar smartphone...")
def load() -> dict:
    con = get_con()
    q = lambda s: con.sql(s).df()  # noqa: E731
    d = {}

    kolom_fact = [r[0] for r in con.execute("DESCRIBE lake.analytics.fact_price").fetchall()]
    has_wil_col = "wilayah_id" in kolom_fact
    wil_sel = "f.wilayah_id" if has_wil_col else "CAST(NULL AS INTEGER) AS wilayah_id"
    seller_sel = "f.seller_name" if "seller_name" in kolom_fact else "CAST(NULL AS VARCHAR) AS seller_name"

    d["fact"] = q(
        f"""
        SELECT f.phone_id, f.marketplace, f.harga, f.harga_asli, f.rating, f.terjual,
               f.layak, f.pasti, {seller_sel}, {wil_sel}, p.brand, p.phone_name,
               p.ram_max_gb, p.storage_max_gb, p.battery_mah, p.release_year
        FROM lake.analytics.fact_price f
        JOIN lake.analytics.dim_phone p USING (phone_id)
        """
    )
    for col in [
        "harga", "harga_asli", "rating", "terjual", "ram_max_gb",
        "storage_max_gb", "battery_mah", "release_year", "wilayah_id",
    ]:
        d["fact"][col] = pd.to_numeric(d["fact"][col], errors="coerce").astype("float64")

    # Muat tabel wilayah (cek lake.analytics.dim_wilayah terlebih dahulu, lalu alternatif skema lake.wilayah)
    d["wil"] = None
    d["wil_status"] = ""
    for tbl_wil in ["lake.analytics.dim_wilayah", "lake.wilayah.dim_wilayah", "lake.wilayah.wilayah"]:
        try:
            df_wil = q(f"SELECT wilayah_id, provinsi, nama, jenis, penduduk FROM {tbl_wil}")
            for col in ["wilayah_id", "penduduk"]:
                df_wil[col] = pd.to_numeric(df_wil[col], errors="coerce").astype("float64")
            d["wil"] = df_wil
            break
        except Exception:  # noqa: BLE001
            continue

    if d["wil"] is None:
        d["wil_status"] = "Tabel `lake.analytics.dim_wilayah` belum ditemukan di katalog DuckLake."
    elif not has_wil_col:
        d["wil_status"] = "Kolom `wilayah_id` belum tersedia di tabel `lake.analytics.fact_price`."
    elif d["fact"]["wilayah_id"].notna().sum() == 0:
        d["wil_status"] = "Kolom `wilayah_id` pada `lake.analytics.fact_price` masih kosong (NULL)."

    d["bh"] = q("SELECT * FROM lake.analytics.banding_harga")
    for col in d["bh"].columns:
        if pd.api.types.is_numeric_dtype(d["bh"][col]) and not pd.api.types.is_bool_dtype(d["bh"][col]):
            d["bh"][col] = d["bh"][col].astype("float64")

    d["yt"] = q(
        """
        SELECT channel, komentar, like_count, tanggal
        FROM lake.youtube.clean_komentar
        WHERE NOT duplikat AND NOT terlalu_pendek AND NOT dari_pemilik_channel
        """
    )
    d["merek"] = q("SELECT * FROM lake.youtube.sebut_merek")
    d["funnel"] = q(
        """
        SELECT 'Tokopedia' AS marketplace,
          (SELECT count(*) FROM lake.tokopedia.clean_listing) AS scrape,
          (SELECT count(*) FROM lake.tokopedia.clean_listing
             WHERE harga_wajar AND bukan_aksesoris) AS filter_ok,
          (SELECT count(*) FROM lake.analytics.fact_price
             WHERE marketplace = 'tokopedia' AND layak) AS terpetakan,
          (SELECT count(*) FROM lake.analytics.fact_price
             WHERE marketplace = 'tokopedia' AND layak AND pasti) AS yakin
        UNION ALL
        SELECT 'Shopee',
          (SELECT count(*) FROM lake.shopee.clean_listing),
          (SELECT count(*) FROM lake.shopee.clean_listing
             WHERE harga_wajar AND bukan_aksesoris AND url_pertama),
          (SELECT count(*) FROM lake.analytics.fact_price
             WHERE marketplace = 'shopee' AND layak),
          (SELECT count(*) FROM lake.analytics.fact_price
             WHERE marketplace = 'shopee' AND layak AND pasti)
        """
    )
    d["n_model_gsm"] = int(q("SELECT count(*) AS n FROM lake.analytics.dim_phone")["n"][0])
    return d


# ============================ SIDEBAR FILTER SEDERHANA ============================
st.sidebar.markdown("### Filter Pencarian")

try:
    D = load()
except Exception as e:  # noqa: BLE001
    st.markdown(
        '<div class="topbar"><div class="eyebrow">Informasi Pasar Smartphone</div>'
        "<h1>Dashboard Harga & Penjualan HP Indonesia</h1>"
        "<p>Data belum siap ditampilkan.</p></div>",
        unsafe_allow_html=True,
    )
    st.error(
        "Database belum ditemukan. Pastikan file katalog DuckLake sudah tersedia di folder proyek.\n\n"
        f"Detail teknis: {e}"
    )
    st.stop()

fact, bh, yt = D["fact"], D["bh"], D["yt"]
base_all = fact[fact["layak"] & fact["pasti"]].copy()
if base_all.empty:
    st.error("Data penjualan masih kosong.")
    st.stop()

brands_all = sorted(base_all["brand"].unique())
brand_sel = st.sidebar.multiselect(
    "Pilih Merek HP", brands_all, default=brands_all,
    help="Pilih satu atau beberapa merek HP yang ingin ditampilkan.",
)
mkt_sel = st.sidebar.multiselect(
    "Pilih Toko Online", ["tokopedia", "shopee"], default=["tokopedia", "shopee"],
    format_func=str.title,
)
lo_jt = float(np.floor(base_all["harga"].min() / 1e6))
hi_jt = float(np.ceil(base_all["harga"].max() / 1e6))
rng = st.sidebar.slider(
    "Sesuaikan Budget (Juta Rp)", lo_jt, hi_jt, (lo_jt, hi_jt), step=0.5,
    help="Geser untuk membatasi rentang harga HP yang ingin dicari.",
)

with st.sidebar.expander("Pengaturan Lanjutan"):
    min_listing = st.slider(
        "Minimal jumlah toko per model HP", 1, 10, 3,
        help="Menyaring model HP agar hanya menampilkan yang dijual oleh minimal sekian toko.",
    )

base = base_all[
    base_all["brand"].isin(brand_sel)
    & base_all["marketplace"].isin(mkt_sel)
    & base_all["harga"].between(rng[0] * 1e6, rng[1] * 1e6)
].copy()
cnt = base.groupby("phone_id")["harga"].transform("size")
base = base[cnt >= min_listing].copy()
if base.empty:
    st.warning("Tidak ada HP yang cocok dengan filter ini. Coba longgarkan pilihan merek atau rentang harga di sebelah kiri.")
    st.stop()

base["segmen"] = pd.cut(base["harga"], SEG_BINS, labels=SEG_LABELS, right=False)
base["harga_jt"] = base["harga"] / 1e6
base["diskon"] = np.where(
    base["harga_asli"] > base["harga"],
    100 * (base["harga_asli"] - base["harga"]) / base["harga_asli"],
    np.nan,
)

models = (
    base.groupby(["phone_id", "phone_name", "brand"], as_index=False)
    .agg(
        listing=("harga", "size"),
        harga_median=("harga", "median"),
        terjual=("terjual", "sum"),
        rating=("rating", "mean"),
        ram=("ram_max_gb", "first"),
        storage=("storage_max_gb", "first"),
        baterai=("battery_mah", "first"),
        tahun=("release_year", "first"),
    )
)

st.sidebar.markdown("---")
st.sidebar.info(
    f"Menampilkan **{len(models)} model HP** dari **{num(len(base))} produk** "
    f"di **{base['brand'].nunique()} merek** terpilih."
)

# ============================ HEADER UTAMA ============================
st.markdown(
    '<div class="topbar"><div class="eyebrow">Informasi Pasar Smartphone Indonesia</div>'
    "<h1>Dashboard Harga & Penjualan HP</h1>"
    "<p>Panduan ringkas harga pasaran, wilayah penjualan terlaris, perbandingan Shopee vs Tokopedia, dan ulasan pembeli</p></div>",
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "Ringkasan & Galeri HP",
    "Sebaran Wilayah & Pasar",
    "Perbandingan Toko & Rekomendasi HP",
    "Ulasan Netizen (YouTube)",
])

# ============================ TAB 1: RINGKASAN & GALERI HP ============================
with tabs[0], guard():
    c = st.columns(4)
    kpi(c[0], "Model HP Tersedia", f"{num(len(models))} model", f"dari {base['brand'].nunique()} merek populer")
    kpi(c[1], "Harga Pasaran (Rata-rata Tengah)", rp(base["harga"].median()), f"Rata-rata semua produk {rp(base['harga'].mean())}")
    kpi(c[2], "Estimasi Unit Terjual", f"{num(base['terjual'].sum())} unit", "berdasarkan label terjual di toko")
    kpi(c[3], "Ulasan Netizen", f"{num(len(yt))} komentar", f"dari {yt['channel'].nunique()} channel review YouTube")

    st.markdown("#### Kesimpulan Singkat Pasar Saat Ini")
    top_brand = base.groupby("brand")["terjual"].sum().sort_values(ascending=False)
    seg_sales = base.groupby("segmen", observed=True)["terjual"].sum()
    b3 = bh[(bh["listing_tokopedia"] >= min_listing) & (bh["listing_shopee"] >= min_listing)
            & bh["brand"].isin(brand_sel)]

    kesimpulan = []
    if top_brand.sum() > 0:
        kesimpulan.append(
            f"**{top_brand.index[0]}** menjadi merek paling laris dengan porsi "
            f"**{top_brand.iloc[0] / top_brand.sum() * 100:.0f}%** dari total penjualan"
            + (f", disusul oleh **{top_brand.index[1]}**." if len(top_brand) > 1 else ".")
        )
    if len(seg_sales) and seg_sales.sum() > 0:
        kesimpulan.append(
            f"HP di kelas harga **{seg_sales.idxmax()}** paling banyak dibeli masyarakat "
            f"(menyumbang **{seg_sales.max() / seg_sales.sum() * 100:.0f}%** total unit terjual)."
        )
    if len(b3):
        lebih_murah = "Shopee" if b3["selisih_pct"].median() < 0 else "Tokopedia"
        kesimpulan.append(
            f"Untuk model HP yang sama di kedua aplikasi, **{lebih_murah}** cenderung menawarkan harga lebih miring "
            f"(rata-rata selisih harga sekitar **{abs(b3['selisih_pct'].median()):.1f}%**)."
        )
    for k_text in kesimpulan:
        insight(k_text)

    st.markdown("#### Galeri HP Terlaris (Klik 'Lihat Detail' untuk Spesifikasi)")
    n_show = st.select_slider("Jumlah HP yang ditampilkan di galeri:", options=[6, 12, 18, 24], value=12)
    top = models.sort_values("terjual", ascending=False).head(n_show).reset_index(drop=True)
    n_cols = 6
    for start_i in range(0, len(top), n_cols):
        cols = st.columns(n_cols)
        for col, (_, row) in zip(cols, top.iloc[start_i:start_i + n_cols].iterrows()):
            with col, st.container(border=True):
                img = phone_img(row["phone_id"])
                if img:
                    st.image(img, width=130)
                else:
                    st.markdown('<div class="noimg">Foto belum<br>tersedia</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="phone-name">{html.escape(str(row["phone_name"]))}</div>'
                    f'<div class="phone-price">{rp(row["harga_median"])}</div>'
                    f'<div class="phone-sold">Terjual ±{num(row["terjual"])}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Lihat detail", key=f"detail_{row['phone_id']}", use_container_width=True):
                    hm = base[base["phone_id"] == row["phone_id"]].groupby("marketplace")["harga"].median()
                    phone_popup(row, hm)

    st.markdown("#### Peringkat Merek Berdasarkan Jumlah Terjual")
    sh = base.groupby("brand", as_index=False)["terjual"].sum().sort_values("terjual")
    fig = px.bar(
        sh, x="terjual", y="brand", orientation="h",
        text_auto=".2s", color_discrete_sequence=[ACCENT],
        title="Total Estimasi Unit Terjual per Merek",
    )
    fig.update_layout(xaxis_title="Estimasi Unit Terjual", yaxis_title="")
    show(fig, 380)


# ============================ TAB 2: SEBARAN WILAYAH & PASAR ============================
with tabs[1], guard():
    st.markdown("#### Produk Terjual per Wilayah")
    wil = D["wil"]
    if wil is None or base["wilayah_id"].notna().sum() == 0:
        if D["wil_status"]:
            st.info(
                f"Data lokasi wilayah penjual belum tersedia di katalog database ({D['wil_status']}).\n\n"
                "Untuk memuat data wilayah ke katalog DuckLake, jalankan secara berurutan di terminal proyek:\n"
                "1. `python SRC/build_local.py`\n"
                "2. `python SRC/publish.py`\n"
                "3. `python SRC/build_lake.py`\n\n"
                "Setelah selesai, muat ulang (refresh) halaman dashboard ini."
            )
        else:
            st.info(
                "Data lokasi wilayah penjual kosong pada kombinasi filter saat ini. "
                "Coba pilih lebih banyak merek atau perluas rentang budget di panel sebelah kiri."
            )
    else:
        bw = base.dropna(subset=["wilayah_id"]).merge(wil, on="wilayah_id", how="left")
        bw["provinsi"] = bw["provinsi"].replace({"Daerah Khusus Ibukota Jakarta": "DKI Jakarta"})
        bw["nama"] = bw["nama"].str.replace(" Administrasi", "", regex=False)

        has_seller = bw["seller_name"].notna().any()
        top_toko = bw.groupby("seller_name")["terjual"].sum().nlargest(5) if has_seller else pd.Series(dtype=float)
        total_all = float(bw["terjual"].sum())
        share_top5 = top_toko.sum() / total_all * 100 if (has_seller and total_all > 0) else 0.0

        if has_seller:
            sembunyi = st.checkbox(
                "Sembunyikan 5 toko raksasa / Official Store teratas (agar sebaran daerah lain lebih terlihat)",
                value=False,
                help="Toko resmi besar di kota besar sering mendominasi angka penjualan. Centang opsi ini untuk melihat sebaran toko reguler di daerah lain.",
            )
            if sembunyi:
                bw = bw[~bw["seller_name"].isin(top_toko.index)].copy()

        if bw.empty:
            st.info("Tidak ada data wilayah tersisa setelah toko teratas disembunyikan.")
        else:
            prov = (
                bw.groupby("provinsi")
                .agg(
                    terjual=("terjual", "sum"),
                    listing=("harga", "size"),
                    toko=("seller_name", "nunique"),
                    kab_kota=("nama", "nunique"),
                )
                .reset_index()
                .sort_values("terjual", ascending=False)
            )
            tot = float(prov["terjual"].sum())
            share = prov["terjual"] / tot * 100 if tot > 0 else prov["terjual"] * 0

            c = st.columns(4)
            kpi(c[0], "Estimasi Unit Terjual (Toko Terdata)", f"{num(tot)} unit", "dari toko yang mencantumkan lokasi")
            kpi(c[1], "Cakupan Daerah", f"{num(bw['nama'].nunique())} Kab/Kota", f"tersebar di {bw['provinsi'].nunique()} provinsi")
            kpi(c[2], "Provinsi Terlaris", prov.iloc[0]["provinsi"], f"menyumbang {share.iloc[0]:.0f}% penjualan")
            kpi(c[3], "Porsi 5 Toko Terbesar", f"{share_top5:.0f}%", "dari seluruh unit terjual")

            top3 = prov.head(3)["provinsi"].tolist()
            insight(
                f"Penjualan HP masih terpusat di **{top3[0]}** ({share.iloc[0]:.0f}% dari total). "
                f"Tiga provinsi teratas (**{', '.join(top3)}**) menguasai **{share.head(3).sum():.0f}%** pasar, "
                f"sementara 5 toko terbesar menyumbang **{share_top5:.0f}%** dari keseluruhan unit terjual."
            )

            a, b = st.columns(2)
            with a:
                t_prov = prov.head(10).sort_values("terjual")
                fig = px.bar(
                    t_prov, x="terjual", y="provinsi", orientation="h",
                    text_auto=".2s", color_discrete_sequence=[ACCENT],
                    hover_data={"listing": True, "toko": True},
                    title="10 Provinsi dengan Penjualan Tertinggi",
                )
                fig.update_layout(xaxis_title="Estimasi Unit Terjual", yaxis_title="")
                show(fig, 400)

            with b:
                kab = (
                    bw.groupby(["nama", "provinsi"], as_index=False)
                    .agg(
                        terjual=("terjual", "sum"),
                        listing=("harga", "size"),
                        toko=("seller_name", "nunique"),
                        harga_median=("harga", "median"),
                        penduduk=("penduduk", "first"),
                    )
                    .sort_values("terjual", ascending=False)
                )
                kab["terjual_per_juta"] = np.where(
                    kab["penduduk"] > 0, kab["terjual"] / kab["penduduk"] * 1e6, np.nan
                )
                t_kab = kab.head(10).sort_values("terjual")
                fig = px.bar(
                    t_kab, x="terjual", y="nama", orientation="h",
                    text_auto=".2s", color_discrete_sequence=[BLUE],
                    hover_data={"provinsi": True, "toko": True},
                    title="10 Kabupaten/Kota dengan Penjualan Tertinggi",
                )
                fig.update_layout(xaxis_title="Estimasi Unit Terjual", yaxis_title="")
                show(fig, 400)

            a, b = st.columns(2)
            with a:
                p6 = prov.head(6)["provinsi"].tolist()
                top_brand6 = bw.groupby("brand")["terjual"].sum().nlargest(6).index
                mb = bw[bw["provinsi"].isin(p6)].copy()
                mb["merek"] = np.where(mb["brand"].isin(top_brand6), mb["brand"], "Lainnya")
                mb = mb.groupby(["provinsi", "merek"], as_index=False)["terjual"].sum()
                fig = px.bar(
                    mb, x="terjual", y="provinsi", color="merek", orientation="h",
                    category_orders={"provinsi": p6[::-1]},
                    title="Merek HP Terlaris di 6 Provinsi Teratas",
                )
                fig.update_layout(barmode="stack", xaxis_title="Estimasi Unit Terjual", yaxis_title="")
                show(fig, 400)

            with b:
                pilih_prov = st.selectbox(
                    "Pilih Provinsi untuk melihat HP paling laris di daerah tersebut:",
                    prov["provinsi"].tolist(),
                    key="prov_model",
                )
                mp = (
                    bw[bw["provinsi"] == pilih_prov]
                    .groupby(["phone_name", "brand"], as_index=False)
                    .agg(terjual=("terjual", "sum"), listing=("harga", "size"))
                    .nlargest(8, "terjual")
                    .sort_values("terjual")
                )
                fig = px.bar(
                    mp, x="terjual", y="phone_name", orientation="h", color="brand",
                    text_auto=".2s", hover_data={"listing": True},
                    title=f"8 Model HP Terlaris di {pilih_prov}",
                )
                fig.update_layout(xaxis_title="Estimasi Unit Terjual", yaxis_title="")
                show(fig, 355)

            with st.expander("Lihat Tabel Lengkap Penjualan per Kabupaten / Kota"):
                st.dataframe(
                    kab[["nama", "provinsi", "terjual", "toko", "listing", "harga_median", "penduduk", "terjual_per_juta"]],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "nama": "Kabupaten / Kota",
                        "provinsi": "Provinsi",
                        "terjual": st.column_config.NumberColumn("Estimasi Unit Terjual", format="%d"),
                        "toko": st.column_config.NumberColumn("Jumlah Toko", format="%d"),
                        "listing": st.column_config.NumberColumn("Jumlah Produk", format="%d"),
                        "harga_median": st.column_config.NumberColumn("Harga Pasaran (Rata-rata Tengah)", format="Rp %d"),
                        "penduduk": st.column_config.NumberColumn("Jumlah Penduduk", format="%d"),
                        "terjual_per_juta": st.column_config.NumberColumn("Terjual per 1 Juta Penduduk", format="%.0f"),
                    },
                )

            warn(
                "**Catatan Penting:** Wilayah di atas menunjukkan **lokasi toko penjual** (asal pengiriman barang), "
                "bukan alamat pembeli. Angka unit terjual dihitung berdasarkan label terjual di marketplace (batas bawah, misalnya '1rb+' dihitung 1.000). "
                "Toko resmi (Official Store) umumnya berpusat di Jabodetabek sehingga angka penjualan di wilayah tersebut terlihat sangat dominan."
            )

    st.markdown("---")
    st.markdown("#### Segmen Harga & Perbandingan Harga per Merek")
    a, b = st.columns(2)
    with a:
        seg = (
            base.groupby("segmen", observed=True)
            .agg(listing=("harga", "size"), terjual=("terjual", "sum"))
            .reset_index()
        )
        seg["Porsi Produk di Toko (%)"] = seg["listing"] / seg["listing"].sum() * 100
        seg["Porsi Unit Terjual (%)"] = seg["terjual"] / max(seg["terjual"].sum(), 1) * 100
        sm = seg.melt(
            id_vars="segmen",
            value_vars=["Porsi Produk di Toko (%)", "Porsi Unit Terjual (%)"],
            var_name="Keterangan",
            value_name="Persen",
        )
        fig = px.bar(
            sm, x="segmen", y="Persen", color="Keterangan", barmode="group",
            color_discrete_sequence=["#94a3b8", ACCENT],
            title="Distribusi Segmen Harga: Stok Toko vs Minat Pembeli",
        )
        fig.update_layout(xaxis_title="Segmen Harga HP", yaxis_title="Persentase (%)")
        show(fig, 400)

    with b:
        br_hrg = (
            base.groupby("brand", as_index=False)["harga_jt"]
            .median()
            .sort_values("harga_jt")
        )
        br_hrg["label_rp"] = br_hrg["harga_jt"].map(lambda x: rp(x * 1e6))
        fig = px.bar(
            br_hrg, x="harga_jt", y="brand", orientation="h",
            text="label_rp", color_discrete_sequence=[BLUE],
            title="Harga Pasaran (Rata-rata Tengah) per Merek",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(xaxis_title="Harga Pasaran (Juta Rp)", yaxis_title="")
        show(fig, 400)


# ============================ TAB 3: PERBANDINGAN TOKO & REKOMENDASI HP ============================
with tabs[2], guard():
    st.markdown("#### Perbandingan Harga Shopee vs Tokopedia")
    cmp_df = bh[
        (bh["listing_tokopedia"] >= min_listing)
        & (bh["listing_shopee"] >= min_listing)
        & bh["brand"].isin(brand_sel)
    ].copy()
    cmp_df["tokped_jt"] = cmp_df["median_tokopedia"] / 1e6
    cmp_df["shopee_jt"] = cmp_df["median_shopee"] / 1e6

    if len(cmp_df) < 3:
        st.info(
            "Model HP yang dijual bersamaan di Shopee dan Tokopedia masih sedikit pada filter ini. "
            "Coba pilih lebih banyak merek di sidebar."
        )
    else:
        sel = cmp_df["selisih_pct"].to_numpy()
        med_sel = float(np.median(sel))

        c = st.columns(3)
        kpi(c[0], "Model HP Dibandingkan", f"{len(cmp_df)} model", "tersedia di Shopee & Tokopedia")
        kpi(c[1], "Shopee Lebih Murah", f"{(sel < 0).mean() * 100:.0f}% model", f"Tokopedia lebih murah di {(sel > 0).mean() * 100:.0f}% model")
        kpi(c[2], "Rata-rata Selisih Harga", f"{abs(med_sel):.1f}%",
            "Shopee cenderung lebih murah" if med_sel < 0 else "Tokopedia cenderung lebih murah")

        if abs(med_sel) < 2.0:
            insight(
                "Secara umum, harga pasaran di **Shopee dan Tokopedia hampir sama** (selisih rata-rata di bawah 2%). "
                "Perbedaan harga lebih bergantung pada promo masing-masing toko."
            )
        elif med_sel < 0:
            insight(
                f"Pada daftar HP yang dibandingkan, **Shopee cenderung lebih murah sekitar {abs(med_sel):.1f}%** "
                "dibandingkan Tokopedia."
            )
        else:
            insight(
                f"Pada daftar HP yang dibandingkan, **Tokopedia cenderung lebih murah sekitar {abs(med_sel):.1f}%** "
                "dibandingkan Shopee."
            )

        nmax = min(20, len(cmp_df))
        nshow = st.slider("Jumlah model HP di grafik perbandingan:", 3, nmax, min(10, nmax), key="nshow") if nmax > 3 else nmax
        t = (
            cmp_df.assign(total=cmp_df["listing_tokopedia"] + cmp_df["listing_shopee"])
            .nlargest(nshow, "total")
            .sort_values("median_tokopedia")
        )
        t_long = t.melt(
            id_vars=["phone_name"],
            value_vars=["tokped_jt", "shopee_jt"],
            var_name="Toko",
            value_name="Harga_Jt",
        )
        t_long["Toko"] = t_long["Toko"].replace({"tokped_jt": "Tokopedia", "shopee_jt": "Shopee"})
        t_long["Label_Rp"] = t_long["Harga_Jt"].map(lambda x: rp(x * 1e6))

        fig = px.bar(
            t_long, x="Harga_Jt", y="phone_name", color="Toko",
            orientation="h", barmode="group", text="Label_Rp",
            color_discrete_map={"Tokopedia": C_TOKPED, "Shopee": C_SHOPEE},
            title="Perbandingan Langsung Harga Pasaran (Juta Rupiah)",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(xaxis_title="Harga Pasaran (Juta Rp)", yaxis_title="")
        show(fig, max(420, nshow * 48))

        with st.expander("Lihat Tabel Perbandingan Harga Lengkap & Unduh Data"):
            tbl = cmp_df[
                ["phone_name", "brand", "median_tokopedia", "median_shopee", "selisih_pct"]
            ].sort_values(by="selisih_pct").copy()
            st.dataframe(
                tbl,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "phone_name": st.column_config.TextColumn("Model HP"),
                    "brand": st.column_config.TextColumn("Merek"),
                    "median_tokopedia": st.column_config.NumberColumn("Harga Pasaran Tokopedia", format="Rp %.0f"),
                    "median_shopee": st.column_config.NumberColumn("Harga Pasaran Shopee", format="Rp %.0f"),
                    "selisih_pct": st.column_config.NumberColumn("Selisih Shopee vs Tokped", format="%+.1f%%"),
                },
            )
            st.download_button(
                "Unduh Tabel Perbandingan (CSV)",
                data=tbl.to_csv(index=False).encode("utf-8"),
                file_name="perbandingan_harga_hp.csv",
                mime="text/csv",
            )

    st.markdown("---")
    st.markdown("#### Rekomendasi HP Paling Worth-It (Spek Tinggi, Harga Terjangkau)")
    sp = models.dropna(subset=["ram", "storage", "baterai", "tahun"]).copy()
    sp = sp[~sp["phone_name"].str.contains("watch", case=False, na=False)].copy()

    if len(sp) < 5:
        st.info("Data spesifikasi belum cukup untuk menampilkan rekomendasi pada filter ini.")
    else:
        pr = lambda s: s.rank(pct=True)  # noqa: E731
        sp["skor_spek"] = (pr(sp["ram"]) + pr(sp["storage"]) + pr(sp["baterai"])) / 3 * 100
        sp["pct_harga"] = pr(sp["harga_median"]) * 100
        sp["worth_it"] = sp["skor_spek"] - sp["pct_harga"]
        sp["Kategori Nilai"] = sp["worth_it"].map(kategori_worth_it)

        insight(
            "Daftar berikut mengelompokkan HP berdasarkan perbandingan **kelengkapan spesifikasi (RAM, Memori, Baterai)** "
            "terhadap **harga pasarannya** agar mudah memilih HP yang paling sesuai dengan kebutuhan dan anggaran."
        )

        v1, v2 = st.columns(2)
        cols = ["phone_name", "harga_median", "ram", "storage", "baterai", "Kategori Nilai"]
        cfg = {
            "phone_name": "Model HP",
            "harga_median": st.column_config.NumberColumn("Harga Pasaran (Rata-rata Tengah)", format="Rp %d"),
            "ram": st.column_config.NumberColumn("RAM", format="%d GB"),
            "storage": st.column_config.NumberColumn("Memori", format="%d GB"),
            "baterai": st.column_config.NumberColumn("Baterai", format="%d mAh"),
            "Kategori Nilai": st.column_config.TextColumn("Penilaian Harga vs Spek"),
        }
        with v1:
            st.markdown("**10 HP Paling Worth-It (Spek Tinggi, Harga Miring)**")
            st.dataframe(sp.nlargest(10, "worth_it")[cols], hide_index=True, use_container_width=True, column_config=cfg)
        with v2:
            st.markdown("**10 HP Kelas Premium / Flagship**")
            st.dataframe(sp.nsmallest(10, "worth_it")[cols], hide_index=True, use_container_width=True, column_config=cfg)


# ============================ TAB 4: ULASAN NETIZEN (YOUTUBE) ============================
with tabs[3], guard():
    if yt.empty:
        st.info("Belum ada data komentar YouTube.")
    else:
        yt = yt.copy()
        yt["teks"] = yt["komentar"].str.lower()
        c = st.columns(3)
        kpi(c[0], "Komentar Dianalisis", f"{num(len(yt))} komentar", "sudah disaring dari spam & komentar singkat")
        kpi(c[1], "Sumber Channel", f"{yt['channel'].nunique()} channel", "kanal review gadget Indonesia")
        kpi(c[2], "Total Apresiasi", f"{num(yt['like_count'].sum())} like", "dukungan pengguna pada komentar")

        TOPIK = {
            "Harga & Promo": r"harga|mahal|murah|budget|juta|\bjt\b|ribu|\brb\b|diskon|promo",
            "Baterai & Charging": r"baterai|batre|battery|\bmah\b|charging|\bcas\b|fast charge",
            "Kamera & Foto": r"kamera|camera|foto|selfie|video",
            "Performa & Gaming": r"performa|game|gaming|ngelag|\blag\b|snapdragon|dimensity|helio|chipset|panas",
            "Kualitas Layar": r"layar|amoled|\blcd\b|refresh|\bhz\b|oled",
            "Software & Update": r"update|software|hyperos|oxygen|one ui|bloatware|iklan|miui",
            "Garansi & Servis": r"garansi|servis|service|\bresmi\b|\bsc\b",
        }
        allt = pd.Series(
            {t_: yt["teks"].str.contains(p, regex=True).mean() * 100 for t_, p in TOPIK.items()}
        ).sort_values()

        insight(
            f"Hal yang paling sering dibahas calon pembeli di YouTube adalah soal **{allt.index[-1]}** "
            f"(muncul di **{allt.iloc[-1]:.0f}%** komentar), diikuti oleh **{allt.index[-2]}** (**{allt.iloc[-2]:.0f}%**)."
        )

        a, b = st.columns(2)
        with a:
            fig = px.bar(
                x=allt.values, y=allt.index, orientation="h",
                text_auto=".1f", color_discrete_sequence=[ACCENT],
                title="Topik yang Paling Sering Dibahas Netizen (%)",
            )
            fig.update_layout(showlegend=False, xaxis_title="Persentase Komentar (%)", yaxis_title="")
            show(fig, 380)

        with b:
            mm = D["merek"].copy()
            mm["merek"] = mm["merek"].replace({"Redmi": "Xiaomi", "Poco": "Xiaomi"})
            buzz = mm.groupby("merek")["jumlah_komentar"].sum()
            sales = base.groupby("brand")["terjual"].sum()
            common = buzz.index.intersection(sales.index)
            if len(common) >= 3 and sales[common].sum() > 0:
                pivot = pd.DataFrame({
                    "Ramai Dibahas di YouTube (%)": buzz[common] / buzz[common].sum() * 100,
                    "Laris Dibeli di Toko (%)": sales[common] / sales[common].sum() * 100,
                })
                long = pivot.reset_index(names="merek").melt(
                    id_vars="merek", var_name="Ukuran", value_name="Persen"
                )
                fig = px.bar(
                    long, x="merek", y="Persen", color="Ukuran", barmode="group",
                    color_discrete_sequence=[BLUE, ACCENT],
                    title="Ramai Dibicarakan vs Benar-Benar Dibeli",
                )
                fig.update_layout(xaxis_title="", yaxis_title="Persentase (%)")
                show(fig, 380)
            else:
                st.info("Pilih lebih banyak merek di sidebar untuk melihat perbandingan ini.")

        st.markdown("#### Komentar Netizen dengan Dukungan (Like) Terbanyak")
        topc = yt.nlargest(10, "like_count")[["channel", "like_count", "komentar"]].copy()
        topc["komentar"] = topc["komentar"].str.slice(0, 220)
        st.dataframe(
            topc, hide_index=True, use_container_width=True,
            column_config={
                "channel": "Channel YouTube",
                "like_count": st.column_config.NumberColumn("Jumlah Like", format="%d"),
                "komentar": "Isi Komentar",
            },
        )


# ============================ INFO TEKNIS (TERLIPAT UNTUK ORANG AWAM) ============================
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("Info Teknis & Sumber Data"):
    st.markdown("##### Alur Pembersihan Data (Dari Hasil Scrape hingga Siap Tampil)")
    f = D["funnel"]
    stages = [
        "Listing hasil scrape",
        "Lolos filter kualitas",
        "Terpetakan ke model GSMArena",
        "Pemetaan yakin (dipakai analisis)",
    ]
    fig = go.Figure()
    for _, r in f.iterrows():
        fig.add_trace(
            go.Funnel(
                name=r["marketplace"],
                y=stages,
                x=[r["scrape"], r["filter_ok"], r["terpetakan"], r["yakin"]],
                textinfo="value+percent initial",
                marker=dict(color=C_TOKPED if r["marketplace"] == "Tokopedia" else C_SHOPEE),
            )
        )
    show(fig, 360)

    a, b = st.columns(2)
    with a:
        st.markdown("**Sumber Tabel Database (DuckLake)**")
        st.dataframe(
            pd.DataFrame({
                "Sumber": ["Tokopedia", "Shopee", "GSMArena", "YouTube", "Wilayah"],
                "Database Lokal": [
                    "tokopedia_lokal.duckdb",
                    "shopee_lokal.duckdb",
                    "gsmarena_lokal.duckdb",
                    "youtube_lokal.duckdb",
                    "wilayah_lokal.duckdb",
                ],
                "Schema Katalog": ["lake.tokopedia", "lake.shopee", "lake.gsmarena", "lake.youtube", "lake.wilayah"],
                "Tabel Analitik": ["fact_price", "fact_price", "dim_phone", "clean_komentar", "dim_wilayah"],
            }),
            hide_index=True,
            use_container_width=True,
        )
    with b:
        st.markdown("**Riwayat Snapshot & Time Travel (DuckLake)**")
        try:
            con = get_con()
            snaps = con.execute("SELECT snapshot_id, snapshot_time, changes FROM lake.snapshots()").df()
            st.dataframe(snaps, hide_index=True, use_container_width=True, height=210)
        except Exception as e:  # noqa: BLE001
            st.info(f"Riwayat snapshot tidak tersedia: {e}")

st.markdown(
    '<div class="footer">Sumber Data: Tokopedia, Shopee, Spesifikasi & Foto GSMArena, serta Komentar YouTube.</div>',
    unsafe_allow_html=True,
)