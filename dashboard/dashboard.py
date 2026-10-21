"""
Dashboard analisis harga HP (Shopee + Tokopedia + GSMArena + komentar YouTube).

"""
import contextlib
import html
import os
import re
import sys
from collections import Counter
from pathlib import Path
import traceback

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

# Path absolut yang dihitung dari lokasi file ini, jadi tidak bergantung pada
# folder tempat Streamlit dijalankan maupun nama user/drive di laptop masing-masing.
# Struktur repo: lakehouse/shared_catalog.ducklake + lakehouse/shared_catalog.ducklake.files/
LAKE_CATALOG = (ROOT / "lakehouse" / "shared_catalog.ducklake").as_posix()
LAKE_DATA = (ROOT / "lakehouse" / "shared_catalog.ducklake.files").as_posix() + "/"

# Palet warna korporat (dipakai di CSS dan semua grafik)
NAVY, ACCENT, BLUE, SLATE = "#0F2D52", "#0E7C86", "#3E6FB0", "#64748B"   # NAVY hanya untuk header; BLUE untuk grafik
C_TOKPED, C_SHOPEE = "#16a34a", "#f97316"      # warna khas masing-masing marketplace
COLORWAY = ["#3E6FB0", "#0E7C86", "#8CA6CF", "#D69E2E", "#7A869A",
            "#C2410C", "#5B8E7D", "#7C6BB5", "#475569", "#B4477A"]
FONT = "Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
SEG_LABELS = ["< 2 jt", "2-4 jt", "4-7 jt", "7-12 jt", "> 12 jt"]
SEG_BINS = [0, 2e6, 4e6, 7e6, 12e6, np.inf]

st.set_page_config(page_title="Dashboard Harga HP", layout="wide")

# Template grafik: font seragam, grid tipis transparan. Warna teks dan latar mengikuti tema
# Streamlit (terang atau gelap), jadi grafik tetap terbaca di kedua tema.
_axis = dict(gridcolor="rgba(128,128,128,0.18)", linecolor="rgba(128,128,128,0.45)",
             zerolinecolor="rgba(128,128,128,0.3)", ticks="outside", tickcolor="rgba(128,128,128,0.45)")
pio.templates["corp"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONT, size=12), colorway=COLORWAY, xaxis=_axis, yaxis=_axis,
))
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

/* Header (selalu navy dengan teks putih, jelas di tema terang maupun gelap) */
.topbar {background: var(--navy); color: #fff; padding: 1.5rem 2rem 1.4rem; border-radius: 6px;
         margin-bottom: 1.2rem; border-bottom: 4px solid var(--accent);}
.topbar .eyebrow {font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
                  color: #9FB6D3; font-weight: 600;}
.topbar h1 {margin: .25rem 0 .3rem; padding: 0; font-size: 1.7rem; font-weight: 700; color: #fff;
            letter-spacing: -.01em;}
.topbar p {margin: 0; color: #C9D6E8; font-size: .92rem;}

/* Tab: warna teks mengikuti tema */
.stTabs [data-baseweb="tab-list"] {gap: 1.7rem; border-bottom: 1px solid var(--line);}
.stTabs [data-baseweb="tab"] {height: 2.9rem; padding: 0 .1rem; background: transparent;}
.stTabs [data-baseweb="tab"] p {font-weight: 600; font-size: .92rem; opacity: .65;}
.stTabs [aria-selected="true"] p {opacity: 1; color: var(--accent);}
.stTabs [data-baseweb="tab-highlight"] {background-color: var(--accent) !important; height: 3px;}
.stTabs [role="tablist"] .react-aria-SelectionIndicator {background-color: var(--accent) !important;}
span[data-baseweb="tag"], span[data-tag] {background-color: var(--accent) !important;}
.stTabs [data-baseweb="tab-border"] {background-color: transparent;}

/* Judul bagian: warna mengikuti tema */
h4, h5 {font-weight: 700; letter-spacing: -.005em; color: inherit;}
h4 {font-size: 1.15rem; margin-top: .6rem;}
h5 {font-size: 1.02rem; margin-top: .4rem;}

/* Kartu KPI: latar transparan netral */
.kpi {background: var(--soft); border: 1px solid var(--line); border-top: 3px solid var(--accent);
      border-radius: 6px; padding: .9rem 1.1rem; min-height: 7.2rem;}
.kpi .l {font-size: .7rem; opacity: .7; text-transform: uppercase; letter-spacing: .08em; font-weight: 600;}
.kpi .v {font-size: 1.5rem; font-weight: 700; line-height: 1.35;}
.kpi .s {font-size: .76rem; opacity: .65;}

/* Catatan */
.insight {border-left: 3px solid var(--accent); background: rgba(14,124,134,.10); padding: .7rem 1rem;
          border-radius: 0 6px 6px 0; margin: .4rem 0; font-size: .93rem;}
.warn {border-left: 3px solid #D69E2E; background: rgba(214,158,46,.12); padding: .7rem 1rem;
       border-radius: 0 6px 6px 0; margin: .4rem 0; font-size: .9rem;}

/* Sidebar */
[data-testid="stSidebar"] {border-right: 1px solid var(--line);}
[data-testid="stSidebar"] h3 {font-size: .76rem; text-transform: uppercase; letter-spacing: .12em;
                              opacity: .7; font-weight: 700;}

/* Galeri HP */
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 8px; border-color: var(--line);}
[data-testid="stImage"] {display: flex; justify-content: center;}
[data-testid="stImage"] img {background: #fff; border-radius: 4px;}
.noimg {width: 130px; height: 173px; margin: 0 auto; background: var(--soft); border: 1px dashed var(--line);
        border-radius: 4px; display: flex; align-items: center; justify-content: center;
        opacity: .75; font-size: .72rem; text-align: center;}
.phone-name {font-size: .84rem; font-weight: 600; line-height: 1.25; min-height: 2.6em;
             text-align: center; margin-top: .35rem;}
.phone-price {font-size: .78rem; opacity: .65; text-align: center; margin-bottom: .45rem;}

/* Tombol dan metrik */
.stButton > button, .stDownloadButton > button {border-radius: 6px; font-weight: 600; font-size: .82rem;}
.stButton > button:hover, .stDownloadButton > button:hover {border-color: var(--accent); color: var(--accent);}
[data-testid="stMetric"] {background: var(--soft); border: 1px solid var(--line); border-radius: 6px;
                          padding: .6rem .8rem;}
[data-testid="stMetricLabel"] p {font-size: .72rem; opacity: .7; text-transform: uppercase; letter-spacing: .05em;}
[data-testid="stMetricValue"] {font-size: 1.25rem;}

/* Footer */
.footer {margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--line);
         opacity: .6; font-size: .78rem; text-align: center;}
</style>
""",
    unsafe_allow_html=True,
)

# Tanpa .streamlit/config.toml, Streamlit memakai warna utama merah. Geser slider ke warna teal
# agar seragam; kalau config.toml sudah dipakai (primaryColor = ACCENT), penyesuaian ini dilewati.
if (st.get_option("theme.primaryColor") or "").lower() != ACCENT.lower():
    st.markdown(
        "<style>[data-testid='stSlider'] {filter: hue-rotate(190deg) saturate(.85) brightness(.9);}</style>",
        unsafe_allow_html=True,
    )


# ============================ helper tampilan ============================
def rp(x) -> str:
    """Format rupiah ringkas: 4,50 jt / 850 rb."""
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
    """Markdown tebal (**x**) -> <b>x</b>, karena markdown tidak diproses di dalam blok HTML."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def insight(text: str):
    st.markdown(f'<div class="insight">{_html(text)}</div>', unsafe_allow_html=True)


def warn(text: str):
    st.markdown(f'<div class="warn">{_html(text)}</div>', unsafe_allow_html=True)


def style(fig, h=420):
    """Judul di pojok kiri atas, legenda tepat di bawah judul (tidak saling menimpa)."""
    ada_judul = bool(fig.layout.title.text)
    ada_legenda = fig.layout.showlegend is not False and sum(
        1 for tr in fig.data if getattr(tr, "showlegend", None) is not False and getattr(tr, "name", None)
    ) >= 2
    top = (36 if ada_judul else 10) + (62 if ada_legenda else 0)
    fig.update_layout(
        height=h,
        margin=dict(l=10, r=10, t=top, b=10),
        title=dict(x=0, xanchor="left", y=0.99, yanchor="top", yref="container",
                   font=dict(size=15, family=FONT)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    title_text="", font=dict(size=11)),
    )
    return fig


@contextlib.contextmanager
def guard():
    """Menampilkan error pada tab terkait dan mencatat traceback."""
    try:
        yield
    except st.errors.StreamlitAPIException:
        raise
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR PADA DASHBOARD")
        traceback.print_exc()
        print("=" * 70 + "\n")

        st.error(
            f"Bagian ini gagal ditampilkan: "
            f"{type(e).__name__}: {e}"
        )
        st.caption(
            "Detail error lengkap tersedia di terminal tempat "
            "Streamlit dijalankan."
        )


def show(fig, h=420):
    st.plotly_chart(style(fig, h), use_container_width=True)


LOG_TICKS = [0.1, 0.2, 0.3, 0.5, 1, 2, 3, 5, 10, 20, 30, 50, 100, 200]


def log_axis(fig, values, axis="y"):
    """Sumbu log dengan tick bersih (1, 2, 3, 5, 10, 20, 50, 100) tanpa label minor yang berantakan."""
    v = pd.Series(values, dtype="float64").dropna()
    v = v[v > 0]
    if v.empty:
        return fig
    lo, hi = v.min() / 1.25, v.max() * 1.25
    ticks = [t for t in LOG_TICKS if lo <= t <= hi]
    if len(ticks) < 3:
        ticks = [t for t in LOG_TICKS if lo / 2 <= t <= hi * 2]
    cfg = dict(type="log", range=[float(np.log10(lo)), float(np.log10(hi))], tickmode="array",
               tickvals=ticks, ticktext=[f"{t:g}".replace(".", ",") for t in ticks])
    (fig.update_yaxes if axis == "y" else fig.update_xaxes)(**cfg)
    return fig


# ============================ [GALERI HP] gambar & pop-up ============================
# Gambar dibuat oleh notebook/05_scraping_gsmarena_images.ipynb -> data/phone_images/<phone_id>.jpg
# (semua berukuran sama, 300x400). phone_id = kunci yang sama dengan dim_phone.
IMG_DIR = ROOT / "data" / "phone_images"


def phone_img(phone_id):
    f = IMG_DIR / f"{phone_id}.jpg"
    return str(f) if f.exists() else None


@st.dialog("Detail HP", width="large")
def phone_popup(row, harga_mkt):
    """Pop-up detail satu model HP. `row` = satu baris dari tabel models."""
    c1, c2 = st.columns([1, 2])
    with c1:
        img = phone_img(row["phone_id"])
        if img:
            st.image(img, width=220)
            st.caption("Gambar: GSMArena")
        else:
            st.info("Gambar belum tersedia untuk model ini.")
    with c2:
        st.markdown(f"### {row['phone_name']}")
        st.caption(f"Merek: {row['brand']}")
        k = st.columns(3)
        k[0].metric("Median harga", rp(row["harga_median"]))
        k[1].metric("Terjual (terlapor)", num(row["terjual"]))
        k[2].metric("Jumlah listing", num(row["listing"]))
        if len(harga_mkt):
            st.markdown("**Median harga per marketplace**")
            for mkt, hrg in harga_mkt.items():
                st.write(f"- {str(mkt).title()}: {rp(hrg)}")
        spek = []
        if pd.notna(row["ram"]):
            spek.append(f"RAM hingga {row['ram']:.0f} GB")
        if pd.notna(row["storage"]):
            spek.append(f"Penyimpanan hingga {row['storage']:.0f} GB")
        if pd.notna(row["baterai"]):
            spek.append(f"Baterai {row['baterai']:.0f} mAh")
        if pd.notna(row["tahun"]):
            spek.append(f"Rilis {row['tahun']:.0f}")
        if spek:
            st.markdown("**Spesifikasi (GSMArena)**")
            st.write(" • ".join(spek))


# ============================ koneksi & data ============================
@st.cache_resource
def get_con():
    con = duckdb.connect()
    con.execute("INSTALL ducklake; LOAD ducklake;")
    # Katalog menyimpan data_path absolut dari laptop pembuatnya (C:/KULIAH/Semester 7/...).
    # DATA_PATH + OVERRIDE_DATA_PATH mengganti path itu dengan folder .files milik repo di komputer ini.
    con.execute(
        f"ATTACH 'ducklake:{LAKE_CATALOG}' AS lake "
        f"(DATA_PATH '{LAKE_DATA}', OVERRIDE_DATA_PATH TRUE, READ_ONLY)"
    )
    return con


@st.cache_data(show_spinner="Memuat data dari katalog...")
def load() -> dict:
    con = get_con()
    q = lambda s: con.sql(s).df()  # noqa: E731
    d = {}
    d["fact"] = q(
        """
        SELECT f.phone_id, f.marketplace, f.harga, f.harga_asli, f.rating, f.terjual,
               f.layak, f.pasti, p.brand, p.phone_name, p.ram_max_gb, p.storage_max_gb,
               p.battery_mah, p.release_year
        FROM lake.analytics.fact_price f
        JOIN lake.analytics.dim_phone p USING (phone_id)
        """
    )
    for col in ["harga", "harga_asli", "rating", "terjual", "ram_max_gb", "storage_max_gb",
                "battery_mah", "release_year"]:
        d["fact"][col] = pd.to_numeric(d["fact"][col], errors="coerce").astype("float64")
    d["bh"] = q("SELECT * FROM lake.analytics.banding_harga")
    for col in d["bh"].columns:  # kolom angka nullable -> float biasa
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


# ============================ sidebar ============================
st.sidebar.markdown("### Filter data")

try:
    D = load()
except Exception as e:  # noqa: BLE001
    st.markdown(
        '<div class="topbar"><div class="eyebrow">Analisis Pasar Smartphone</div>'
        "<h1>Dashboard Harga HP Indonesia</h1>"
        "<p>Data belum bisa dimuat.</p></div>",
        unsafe_allow_html=True,
    )
    st.error(
        "Gagal membaca data. Urutan yang benar dari folder utama proyek: "
        "`python SRC/build_local.py` → `python SRC/publish.py` → `python SRC/build_lake.py`.\n\n"
        f"Detail: {e}"
    )
    st.stop()

fact, bh, yt = D["fact"], D["bh"], D["yt"]
base_all = fact[fact["layak"] & fact["pasti"]].copy()
if base_all.empty:
    st.error("Tabel fact_price kosong. Jalankan ulang tahap build_lake.")
    st.stop()

brands_all = sorted(base_all["brand"].unique())
brand_sel = st.sidebar.multiselect("Merek", brands_all, default=brands_all)
mkt_sel = st.sidebar.multiselect(
    "Marketplace", ["tokopedia", "shopee"], default=["tokopedia", "shopee"],
    format_func=str.title,
)
lo_jt = float(np.floor(base_all["harga"].min() / 1e6))
hi_jt = float(np.ceil(base_all["harga"].max() / 1e6))
rng = st.sidebar.slider("Rentang harga (juta Rp)", lo_jt, hi_jt, (lo_jt, hi_jt), step=0.5)
min_listing = st.sidebar.slider("Minimal listing per model", 1, 10, 3)

base = base_all[
    base_all["brand"].isin(brand_sel)
    & base_all["marketplace"].isin(mkt_sel)
    & base_all["harga"].between(rng[0] * 1e6, rng[1] * 1e6)
].copy()
cnt = base.groupby("phone_id")["harga"].transform("size")
base = base[cnt >= min_listing].copy()
if base.empty:
    st.warning("Tidak ada data dengan filter ini. Longgarkan filter di sidebar.")
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
st.sidebar.caption(
    f"**{num(len(base))}** listing • **{len(models)}** model • "
    f"**{base['brand'].nunique()}** merek terpilih"
)

# ============================ header ============================
st.markdown(
    '<div class="topbar"><div class="eyebrow">Analisis Pasar Smartphone</div>'
    "<h1>Dashboard Harga HP Indonesia</h1>"
    "<p>Gabungan data Tokopedia, Shopee, spesifikasi GSMArena, dan komentar YouTube</p></div>",
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "Ringkasan", "Pasar & Harga", "Shopee vs Tokopedia",
    "Spesifikasi vs Harga", "Komentar", "Kualitas Data",
])

# ============================ TAB 1: RINGKASAN ============================
with tabs[0], guard():
    c = st.columns(5)
    kpi(c[0], "Model terpetakan", num(len(models)), f"dari {D['n_model_gsm']} model GSMArena")
    kpi(c[1], "Listing dianalisis", num(len(base)),
        f"Tokopedia {num((base.marketplace == 'tokopedia').sum())} • "
        f"Shopee {num((base.marketplace == 'shopee').sum())}")
    kpi(c[2], "Median harga", rp(base["harga"].median()), f"Rata-rata {rp(base['harga'].mean())}")
    kpi(c[3], "Total terjual (terlapor)", num(base["terjual"].sum()), "jumlah di label marketplace")
    kpi(c[4], "Komentar YouTube bersih", num(len(yt)), f"{yt['channel'].nunique()} channel")

    st.markdown("#### Temuan utama")
    top_brand = base.groupby("brand")["terjual"].sum().sort_values(ascending=False)
    seg_sales = base.groupby("segmen", observed=True)["terjual"].sum()
    seg_list = base["segmen"].value_counts()
    if top_brand.sum() > 0:
        insight(
            f"**{top_brand.index[0]}** memimpin penjualan terlapor "
            f"({top_brand.iloc[0] / top_brand.sum() * 100:.0f}% dari total)"
            + (f", diikuti **{top_brand.index[1]}**." if len(top_brand) > 1 else ".")
        )
    if len(seg_sales) and seg_sales.sum() > 0:
        insight(
            f"Segmen **{seg_sales.idxmax()}** menyumbang "
            f"{seg_sales.max() / seg_sales.sum() * 100:.0f}% penjualan, sedangkan segmen dengan listing "
            f"terbanyak adalah **{seg_list.idxmax()}** ({seg_list.max() / len(base) * 100:.0f}% listing)."
        )
    b3 = bh[(bh["listing_tokopedia"] >= min_listing) & (bh["listing_shopee"] >= min_listing)
            & bh["brand"].isin(brand_sel)]
    if len(b3):
        insight(
            f"Dari **{len(b3)}** model yang ada di kedua marketplace, Shopee lebih murah di "
            f"**{(b3['selisih_pct'] < 0).mean() * 100:.0f}%** model; median selisih harga "
            f"**{b3['selisih_pct'].median():+.1f}%** (positif = Shopee lebih mahal)."
        )
    else:
        warn("Belum ada model dengan data cukup di kedua marketplace pada filter ini.")

    # [GALERI HP] menggantikan treemap "Peta pasar"
    st.markdown("##### Galeri HP terlaris (urut penjualan terlapor)")
    n_show = st.select_slider("Jumlah HP ditampilkan", options=[6, 12, 18, 24], value=12)
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
                    st.markdown('<div class="noimg">Foto belum tersedia</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="phone-name">{html.escape(str(row["phone_name"]))}</div>'
                    f'<div class="phone-price">{rp(row["harga_median"])}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Lihat detail", key=f"detail_{row['phone_id']}", use_container_width=True):
                    hm = base[base["phone_id"] == row["phone_id"]].groupby("marketplace")["harga"].median()
                    phone_popup(row, hm)

    sh = base.groupby("brand", as_index=False)["terjual"].sum().sort_values("terjual")
    fig = px.bar(sh, x="terjual", y="brand", orientation="h",
                 color_discrete_sequence=[ACCENT], title="Penjualan terlapor per merek")
    fig.update_layout(xaxis_title="Unit terjual (terlapor)", yaxis_title="")
    show(fig, 400)

# ============================ TAB 2: PASAR & HARGA ============================
with tabs[1], guard():
    a, b = st.columns(2)
    with a:
        order = base.groupby("brand")["harga_jt"].median().sort_values().index.tolist()
        fig = go.Figure()
        for br in order:
            fig.add_trace(go.Box(y=base.loc[base["brand"] == br, "harga_jt"].to_numpy(), name=str(br),
                                 boxpoints=False, line=dict(color=ACCENT, width=1.5),
                                 fillcolor="rgba(14,124,134,0.22)"))
        fig.update_layout(showlegend=False, title="Sebaran harga per merek (skala log)",
                          xaxis_title="", yaxis_title="Harga (juta Rp)")
        log_axis(fig, base["harga_jt"], "y")
        show(fig)
    with b:
        seg = (base.groupby("segmen", observed=True)
               .agg(listing=("harga", "size"), terjual=("terjual", "sum")).reset_index())
        seg["Share listing"] = seg["listing"] / seg["listing"].sum() * 100
        seg["Share penjualan"] = seg["terjual"] / max(seg["terjual"].sum(), 1) * 100
        sm = seg.melt(id_vars="segmen", value_vars=["Share listing", "Share penjualan"],
                      var_name="Ukuran", value_name="Persen")
        fig = px.bar(sm, x="segmen", y="Persen", color="Ukuran", barmode="group",
                     color_discrete_sequence=["#94a3b8", ACCENT],
                     title="Segmen harga: pasokan (listing) vs permintaan (penjualan)")
        fig.update_layout(xaxis_title="Segmen harga", yaxis_title="% dari total")
        show(fig)
        gap = seg.assign(selisih=seg["Share penjualan"] - seg["Share listing"])
        if gap["selisih"].abs().max() > 3:
            r = gap.loc[gap["selisih"].abs().idxmax()]
            arah = "lebih tinggi" if r["selisih"] > 0 else "lebih rendah"
            insight(f"Segmen **{r['segmen']}**: share penjualan {abs(r['selisih']):.0f} poin {arah} "
                    "daripada share listing-nya.")

    a, b = st.columns(2)
    with a:
        topn = st.slider("Jumlah model terlaris", 5, 25, 10, key="topn")
        t = models.nlargest(topn, "terjual").sort_values("terjual")
        fig = px.bar(t, x="terjual", y="phone_name", orientation="h", color="brand",
                     title=f"{topn} model terlaris (penjualan terlapor)",
                     hover_data={"harga_median": ":,.0f", "listing": True})
        fig.update_layout(xaxis_title="Unit terjual (terlapor)", yaxis_title="")
        show(fig, 460)
    with b:
        fig = px.histogram(base, x="harga_jt", color="marketplace", nbins=40, barmode="overlay",
                           opacity=.65,
                           color_discrete_map={"tokopedia": C_TOKPED, "shopee": C_SHOPEE},
                           title="Distribusi harga listing per marketplace")
        fig.update_layout(xaxis_title="Harga (juta Rp)", yaxis_title="Jumlah listing")
        show(fig, 460)

    st.markdown("##### Diskon")
    disc = base.assign(ada_diskon=base["diskon"].notna())
    d1, d2 = st.columns(2)
    with d1:
        g = disc.groupby("marketplace").agg(
            pct_ada=("ada_diskon", "mean"), rata=("diskon", "mean")).reset_index()
        g["pct_ada"] *= 100
        fig = go.Figure()
        fig.add_bar(x=g["marketplace"].str.title(), y=g["pct_ada"], name="% listing berdiskon",
                    marker_color="#94a3b8")
        fig.add_bar(x=g["marketplace"].str.title(), y=g["rata"].fillna(0),
                    name="Rata-rata besar diskon (%)", marker_color=ACCENT)
        fig.update_layout(barmode="group", title="Intensitas diskon per marketplace")
        show(fig, 340)
    with d2:
        g2 = disc.dropna(subset=["diskon"]).groupby("brand")["diskon"].agg(["mean", "size"]).reset_index()
        g2 = g2[g2["size"] >= 5].sort_values("mean")
        if len(g2):
            fig = px.bar(g2, x="mean", y="brand", orientation="h",
                         color_discrete_sequence=[BLUE],
                         title="Rata-rata diskon per merek (min. 5 listing berdiskon)")
            fig.update_layout(xaxis_title="Diskon (%)", yaxis_title="")
            show(fig, 340)
        else:
            st.info("Data diskon belum cukup per merek.")
    warn("Catatan: 'terjual' adalah angka yang tertulis di label marketplace "
         "(misal '10RB+' dihitung 10.000), jadi merupakan batas bawah, bukan angka pasti.")

# ============================ TAB 3: SHOPEE VS TOKOPEDIA ============================
with tabs[2], guard():
    cmp_df = bh[(bh["listing_tokopedia"] >= min_listing) & (bh["listing_shopee"] >= min_listing)
                & bh["brand"].isin(brand_sel)].copy()
    cmp_df["tokped_jt"] = cmp_df["median_tokopedia"] / 1e6
    cmp_df["shopee_jt"] = cmp_df["median_shopee"] / 1e6
    if len(cmp_df) < 3:
        st.info("Model yang tersedia di kedua marketplace masih terlalu sedikit untuk dibandingkan. "
                "Turunkan 'Minimal listing per model' atau tambah merek di sidebar.")
    else:
        sel = cmp_df["selisih_pct"].to_numpy()
        boots = np.random.default_rng(42).choice(sel, size=(2000, len(sel)), replace=True)
        ci = np.percentile(np.median(boots, axis=1), [2.5, 97.5])

        c = st.columns(4)
        kpi(c[0], "Model dibandingkan", len(cmp_df), f"min. {min_listing} listing/marketplace")
        kpi(c[1], "Shopee lebih murah di", f"{(sel < 0).mean() * 100:.0f}%", "dari model yang dibandingkan")
        kpi(c[2], "Median selisih", f"{np.median(sel):+.1f}%", "positif = Shopee lebih mahal")
        kpi(c[3], "Rentang tak-pasti (95%)", f"{ci[0]:+.1f}% s/d {ci[1]:+.1f}%", "bootstrap median selisih")

        if ci[0] < 0 < ci[1]:
            insight("Rentang ketidakpastian **mencakup 0%**: berdasarkan data ini belum ada bukti kuat "
                    "bahwa salah satu marketplace secara konsisten lebih murah.")
        elif ci[0] >= 0:
            insight("Rentang ketidakpastian berada di **atas 0%**: Shopee cenderung lebih mahal "
                    "dibanding Tokopedia pada sampel ini.")
        else:
            insight("Rentang ketidakpastian berada di **bawah 0%**: Shopee cenderung lebih murah "
                    "dibanding Tokopedia pada sampel ini.")

        a, b = st.columns(2)
        with a:
            nmax = min(30, len(cmp_df))
            if nmax > 3:
                nshow = st.slider("Jumlah model di grafik", 3, nmax, min(12, nmax), key="nshow")
            else:
                nshow = nmax
            t = (cmp_df.assign(total=cmp_df["listing_tokopedia"] + cmp_df["listing_shopee"])
                 .nlargest(nshow, "total").sort_values("selisih_pct"))
            xs, ys = [], []
            for _, r in t.iterrows():
                xs += [r["tokped_jt"], r["shopee_jt"], None]
                ys += [r["phone_name"], r["phone_name"], None]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#94a3b8", width=2),
                                     hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scatter(x=t["tokped_jt"], y=t["phone_name"], mode="markers", name="Tokopedia",
                                     marker=dict(color=C_TOKPED, size=11)))
            fig.add_trace(go.Scatter(x=t["shopee_jt"], y=t["phone_name"], mode="markers", name="Shopee",
                                     marker=dict(color=C_SHOPEE, size=11)))
            fig.update_layout(title="Perbandingan Harga Median Smartphone di Shopee dan Tokopedia",
                              xaxis_title="Harga (juta Rp)", yaxis_title="")
            show(fig, 480)
        with b:
            lim = [min(cmp_df["tokped_jt"].min(), cmp_df["shopee_jt"].min()) * .9,
                   max(cmp_df["tokped_jt"].max(), cmp_df["shopee_jt"].max()) * 1.1]
            fig = px.scatter(cmp_df, x="tokped_jt", y="shopee_jt", color="brand", hover_name="phone_name",
                             log_x=True, log_y=True,
                             title="Hubungan Harga Smartphone antara Tokopedia dan Shopee")
            fig.add_trace(go.Scatter(x=lim, y=lim, mode="lines", line=dict(dash="dash", color="#64748b"),
                                     name="Harga sama", hoverinfo="skip"))
            fig.update_layout(xaxis_title="Median Tokopedia (juta Rp)", yaxis_title="Median Shopee (juta Rp)")
            both = pd.concat([cmp_df["tokped_jt"], cmp_df["shopee_jt"]])
            log_axis(fig, both, "x")
            log_axis(fig, both, "y")
            show(fig, 480)

        a, b = st.columns(2)
        with a:
            fig = px.histogram(cmp_df, x="selisih_pct", nbins=15, color_discrete_sequence=[ACCENT],
                               title="Distribusi Persentase Selisih Harga Shopee terhadap Tokopedia")
            fig.add_vline(x=0, line_dash="dash", line_color="#64748b")
            fig.add_vline(x=float(np.median(sel)), line_color="#f97316")
            fig.update_layout(xaxis_title="Selisih (%)", yaxis_title="Jumlah model")
            show(fig, 380)
        with b:
            gb = (cmp_df.groupby("brand")["selisih_pct"].agg(["mean", "size"]).reset_index()
                  .query("size >= 2").sort_values("mean"))
            if len(gb):
                fig = px.bar(gb, x="mean", y="brand", orientation="h", color="mean",
                             color_continuous_scale="RdYlGn_r", color_continuous_midpoint=0,
                             title="Perbandingan Selisih Harga Antar-Brand di Kedua Marketplace")
                fig.update_layout(xaxis_title="Selisih (%)", yaxis_title="", coloraxis_showscale=False)
                show(fig, 380)
            else:
                st.info("Belum ada merek dengan minimal 2 model yang dibandingkan.")
        st.markdown("##### Tabel perbandingan Harga Smartphone per Model")

        tbl = (
            cmp_df[
                [
                    "phone_name",
                    "brand",
                    "listing_tokopedia",
                    "listing_shopee",
                    "median_tokopedia",
                    "median_shopee",
                    "selisih_pct",
                ]
            ]
            .sort_values(by="selisih_pct")
            .copy()
        )

        # Gunakan format tampilan sederhana terlebih dahulu
        st.dataframe(
            tbl,
            use_container_width=True,
            hide_index=True,
            column_config={
                "phone_name": st.column_config.TextColumn("Model"),
                "brand": st.column_config.TextColumn("Merek"),
                "listing_tokopedia": st.column_config.NumberColumn(
                    "Listing Tokped", format="%d"
                ),
                "listing_shopee": st.column_config.NumberColumn(
                    "Listing Shopee", format="%d"
                ),
                "median_tokopedia": st.column_config.NumberColumn(
                    "Median Tokopedia", format="Rp %.0f"
                ),
                "median_shopee": st.column_config.NumberColumn(
                    "Median Shopee", format="Rp %.0f"
                ),
                "selisih_pct": st.column_config.NumberColumn(
                    "Selisih (%)", format="%+.1f%%"
                ),
            },
        )

        st.download_button(
            "Unduh CSV",
            data=tbl.to_csv(index=False).encode("utf-8"),
            file_name="banding_harga.csv",
            mime="text/csv",
        )

        warn(f"Ukuran sampel kecil ({len(cmp_df)} model). Median per model dihitung dari "
             "sedikit listing di Shopee, jadi baca hasil ini sebagai indikasi, bukan kesimpulan pasti.")

# ============================ TAB 4: SPESIFIKASI VS HARGA ============================
with tabs[3], guard():
    sp = models.dropna(subset=["ram", "storage", "baterai", "tahun"]).copy()
    if len(sp) < 8:
        st.info("Model dengan spesifikasi lengkap terlalu sedikit pada filter ini.")
    else:
        sp["harga_jt"] = sp["harga_median"] / 1e6
        LABEL = {"ram": "RAM maksimum (GB)", "storage": "Penyimpanan maksimum (GB)",
                 "baterai": "Baterai (mAh)", "tahun": "Tahun rilis"}
        xvar = st.selectbox("Bandingkan harga dengan", list(LABEL), format_func=LABEL.get)
        a, b = st.columns([3, 2])
        with a:
            fig = px.scatter(sp, x=xvar, y="harga_jt", color="brand", size=sp["terjual"].clip(lower=1),
                             size_max=34, hover_name="phone_name", log_y=True,
                             title="Hubungan Spesifikasi Smartphone dengan Harga dan Penjualan")
            if sp[xvar].nunique() > 2:
                k, c0 = np.polyfit(sp[xvar], np.log(sp["harga_jt"]), 1)
                xs = np.linspace(sp[xvar].min(), sp[xvar].max(), 50)
                fig.add_trace(go.Scatter(x=xs, y=np.exp(c0 + k * xs), mode="lines",
                                         line=dict(color="#64748b", dash="dash"), name="Tren"))
            fig.update_layout(xaxis_title=LABEL[xvar], yaxis_title="Median harga (juta Rp)")
            log_axis(fig, sp["harga_jt"], "y")
            show(fig, 470)
        with b:
            cm = sp[["harga_median", "ram", "storage", "baterai", "tahun"]].rank().corr()
            cm.index = cm.columns = ["Harga", "RAM", "Storage", "Baterai", "Tahun"]
            fig = px.imshow(cm.round(2), text_auto=True, color_continuous_scale="RdBu_r",
                            zmin=-1, zmax=1, title="Hubungan Spesifikasi dengan Harga Smartphone")
            show(fig, 470)

        st.markdown("##### Estimasi Perubahan Harga Berdasarkan Peningkatan Spesifikasi")
        if len(sp) >= 15:
            X = np.column_stack([np.ones(len(sp)), sp["ram"], sp["storage"] / 128,
                                 sp["baterai"] / 1000, sp["tahun"] - sp["tahun"].min()])
            y = np.log(sp["harga_median"].to_numpy())
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            res = y - X @ beta
            r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
            sigma2 = (res ** 2).sum() / (len(y) - X.shape[1])
            se = np.sqrt(np.diag(sigma2 * np.linalg.pinv(X.T @ X)))
            out = pd.DataFrame({
                "Peningkatan": ["+1 GB RAM", "+128 GB penyimpanan", "+1.000 mAh baterai", "+1 tahun lebih baru"],
                "Perkiraan perubahan harga (%)": (np.exp(beta[1:]) - 1) * 100,
                "Kemungkinan harga terendah (%)": (np.exp(beta[1:] - 1.96 * se[1:]) - 1) * 100,
                "Kemungkinan harga tertinggi (%)": (np.exp(beta[1:] + 1.96 * se[1:]) - 1) * 100,
            })
            st.dataframe(out.round(1), hide_index=True, use_container_width=True)
            insight(f"Regresi sederhana ini menjelaskan sekitar **{r2 * 100:.0f}%** variasi harga "
                    f"({len(sp)} model). Interval yang melewati 0% berarti efeknya belum jelas.")
            warn("Indikatif saja: RAM, penyimpanan, dan merek saling berkaitan (multikolinearitas), "
                 "dan merek/chipset belum dimasukkan ke model.")
        else:
            st.info("Perlu minimal 15 model dengan spesifikasi lengkap untuk regresi.")

        st.markdown("##### Model Smartphone dengan Nilai Spesifikasi Terbaik terhadap Harga")
        pr = lambda s: s.rank(pct=True)  # noqa: E731
        sp = sp[~sp["phone_name"].str.contains("watch", case=False, na=False)].copy()
        sp["skor_spek"] = (pr(sp["ram"]) + pr(sp["storage"]) + pr(sp["baterai"])) / 3 * 100
        sp["pct_harga"] = pr(sp["harga_median"]) * 100
        sp["worth_it"] = sp["skor_spek"] - sp["pct_harga"]
        v1, v2 = st.columns(2)
        cols = ["phone_name", "harga_median", "skor_spek", "pct_harga", "worth_it"]
        cfg = {
            "phone_name": "Model",
            "harga_median": st.column_config.NumberColumn("Median harga", format="Rp %d"),
            "skor_spek": st.column_config.NumberColumn("Skor spek", format="%.0f"),
            "pct_harga": st.column_config.NumberColumn("Persentil harga", format="%.0f"),
            "worth_it": st.column_config.NumberColumn("Worth-it", format="%+.0f"),
        }
        with v1:
            st.caption("Smartphone dengan Spesifikasi Tinggi Relatif terhadap Harga")
            st.dataframe(sp.nlargest(10, "worth_it")[cols], hide_index=True, use_container_width=True,
                         column_config=cfg)
        with v2:
            st.caption("Smartphone dengan Harga Relatif Tinggi terhadap Spesifikasi")
            st.dataframe(sp.nsmallest(10, "worth_it")[cols], hide_index=True, use_container_width=True,
                         column_config=cfg)
        st.caption("Skor spek = rata-rata persentil RAM, penyimpanan, dan baterai. "
                   "Worth-it = skor spek dikurangi persentil harga. Tidak menilai kamera, layar, atau chipset.")

# ============================ TAB 5: KOMENTAR ============================
with tabs[4], guard():
    if yt.empty:
        st.info("Belum ada data komentar.")
    else:
        yt = yt.copy()
        yt["teks"] = yt["komentar"].str.lower()
        c = st.columns(4)
        kpi(c[0], "Komentar bersih", num(len(yt)), "tanpa duplikat, terlalu pendek, atau dari pemilik channel")
        kpi(c[1], "Channel", yt["channel"].nunique(), "")
        kpi(c[2], "Median panjang", f"{yt['komentar'].str.len().median():.0f} karakter", "")
        kpi(c[3], "Total like", num(yt["like_count"].sum()), "")

        a, b = st.columns(2)
        with a:
            cc = yt["channel"].value_counts().reset_index()
            cc.columns = ["channel", "komentar"]
            fig = px.bar(cc.sort_values("komentar"), x="komentar", y="channel", orientation="h",
                         color_discrete_sequence=[BLUE], title="Komentar per channel")
            fig.update_layout(yaxis_title="", xaxis_title="Jumlah komentar")
            show(fig, 340)
        with b:
            mo = yt.assign(bulan=yt["tanggal"].dt.to_period("M").dt.to_timestamp())
            mo = mo.groupby(["bulan", "channel"]).size().reset_index(name="komentar")
            fig = px.line(mo, x="bulan", y="komentar", color="channel", markers=True,
                          title="Komentar per bulan")
            fig.update_layout(xaxis_title="", yaxis_title="Jumlah komentar")
            show(fig, 340)

        TOPIK = {
            "Harga": r"harga|mahal|murah|budget|juta|\bjt\b|ribu|\brb\b|diskon|promo",
            "Baterai & charging": r"baterai|batre|battery|\bmah\b|charging|\bcas\b|fast charge",
            "Kamera": r"kamera|camera|foto|selfie|video",
            "Performa & game": r"performa|game|gaming|ngelag|\blag\b|snapdragon|dimensity|helio|chipset|panas",
            "Layar": r"layar|amoled|\blcd\b|refresh|\bhz\b|oled",
            "Software & update": r"update|software|hyperos|oxygen|one ui|bloatware|iklan|miui",
            "Garansi & servis": r"garansi|servis|service|\bresmi\b|\bsc\b",
        }
        rows = []
        for ch, g in yt.groupby("channel"):
            for t_, pat in TOPIK.items():
                rows.append({"channel": ch, "topik": t_,
                             "persen": g["teks"].str.contains(pat, regex=True).mean() * 100})
        tp = pd.DataFrame(rows)
        a, b = st.columns([3, 2])
        with a:
            hm = tp.pivot(index="topik", columns="channel", values="persen")
            fig = px.imshow(hm.round(1), text_auto=True, aspect="auto", color_continuous_scale="Tealgrn",
                            title="Topik yang dibahas (% komentar yang menyebut topik)")
            show(fig, 400)
        with b:
            allt = pd.Series({t_: yt["teks"].str.contains(p, regex=True).mean() * 100
                              for t_, p in TOPIK.items()}).sort_values()
            fig = px.bar(x=allt.values, y=allt.index, orientation="h",
                         color_discrete_sequence=[ACCENT], title="Topik terpopuler (semua channel)")
            fig.update_layout(showlegend=False, xaxis_title="% komentar", yaxis_title="")
            show(fig, 400)
        insight(f"Topik yang paling sering dibahas: **{allt.index[-1]}** "
                f"({allt.iloc[-1]:.0f}% komentar), disusul **{allt.index[-2]}** ({allt.iloc[-2]:.0f}%).")

        st.markdown("##### Obrolan vs penjualan per merek")
        mm = D["merek"].copy()
        mm["merek"] = mm["merek"].replace({"Redmi": "Xiaomi", "Poco": "Xiaomi"})
        buzz = mm.groupby("merek")["jumlah_komentar"].sum()
        sales = base.groupby("brand")["terjual"].sum()
        common = buzz.index.intersection(sales.index)
        if len(common) >= 3 and sales[common].sum() > 0:
            pivot = pd.DataFrame({
                "Share obrolan (%)": buzz[common] / buzz[common].sum() * 100,
                "Share penjualan (%)": sales[common] / sales[common].sum() * 100,
            })
            long = pivot.reset_index(names="merek").melt(id_vars="merek", var_name="Ukuran", value_name="Persen")
            fig = px.bar(long, x="merek", y="Persen", color="Ukuran", barmode="group",
                         color_discrete_sequence=[BLUE, ACCENT],
                         title="Merek yang sering dibicarakan vs merek yang laris")
            fig.update_layout(xaxis_title="", yaxis_title="% dari total (merek yang dibandingkan)")
            show(fig, 380)
            diff = (pivot["Share obrolan (%)"] - pivot["Share penjualan (%)"]).sort_values()
            insight(f"**{diff.index[-1]}** paling 'ramai dibicarakan' dibanding penjualannya "
                    f"({diff.iloc[-1]:+.0f} poin), sedangkan **{diff.index[0]}** paling 'laris tapi sepi "
                    f"dibahas' ({diff.iloc[0]:+.0f} poin).")
            warn("Deteksi merek di komentar memakai kata kunci sederhana, dan komentar YouTube berasal "
                 "dari 4 channel saja, jadi ini bukan representasi seluruh pasar.")
        else:
            st.info("Merek yang bisa dibandingkan terlalu sedikit pada filter ini.")

        a, b = st.columns(2)
        with a:
            STOP = set("""yang dan di ke dari ini itu untuk dengan atau juga nya aja gak ga tidak yg udah sudah
            saya gue gw bang bro kak kok sih lah dong deh ada bisa banget lebih kalau kalo jadi pakai pake buat
            karena tapi pada sama masih mau lagi cuma hanya punya apa nih tuh emang pas udh bgt jg dr tp dgn sy
            krn kan lu loh amp quot ngga nggak aku kita dia kamu mas mba mbak bukan kenapa gimana
            bagus banyak dulu pun saja sangat harus orang tau tahu lain sekali apakah""".split())
            words = Counter(w for t_ in yt["teks"] for w in re.findall(r"[a-z0-9]{3,}", t_) if w not in STOP)
            wf = pd.DataFrame(words.most_common(20), columns=["kata", "jumlah"]).sort_values("jumlah")
            fig = px.bar(wf, x="jumlah", y="kata", orientation="h", color_discrete_sequence=["#64748b"],
                         title="20 kata paling sering muncul")
            fig.update_layout(yaxis_title="", xaxis_title="Frekuensi")
            show(fig, 520)
        with b:
            st.caption("Komentar dengan like terbanyak")
            topc = yt.nlargest(10, "like_count")[["channel", "like_count", "komentar"]].copy()
            topc["komentar"] = topc["komentar"].str.slice(0, 180)
            st.dataframe(topc, hide_index=True, use_container_width=True, height=520,
                         column_config={"channel": "Channel",
                                        "like_count": st.column_config.NumberColumn("Like", format="%d"),
                                        "komentar": "Komentar"})
        warn("Komentar YouTube belum bisa dikaitkan ke model HP tertentu karena data scrape tidak memuat "
             "ID/judul video. Analisis di tab ini bersifat per channel dan per merek.")

# ============================ TAB 6: KUALITAS DATA ============================
with tabs[5], guard():
    st.markdown("##### Dari data mentah ke data siap analisis")
    f = D["funnel"]
    stages = ["Listing hasil scrape", "Lolos filter kualitas", "Terpetakan ke model GSMArena",
              "Pemetaan yakin (dipakai analisis)"]
    fig = go.Figure()
    for _, r in f.iterrows():
        fig.add_trace(go.Funnel(
            name=r["marketplace"], y=stages, x=[r["scrape"], r["filter_ok"], r["terpetakan"], r["yakin"]],
            textinfo="value+percent initial",
            marker=dict(color=C_TOKPED if r["marketplace"] == "Tokopedia" else C_SHOPEE)))
    show(fig, 400)
    st.caption("Filter kualitas: harga wajar (Rp 300 rb - 90 jt), bukan aksesoris, dan URL unik. "
               "Pemetaan 'yakin' = tidak ada model lain yang sama spesifiknya, atau cocok dengan keyword pencarian.")

    a, b = st.columns(2)
    with a:
        cov = base_all.groupby("phone_id")["marketplace"].nunique()
        n_both = int((cov == 2).sum())
        n_one = int((cov == 1).sum())
        n_none = max(D["n_model_gsm"] - n_both - n_one, 0)
        cv = pd.DataFrame({"Status": ["Ada di kedua marketplace", "Hanya satu marketplace",
                                      "Tidak ada listing"], "Model": [n_both, n_one, n_none]})
        fig = px.pie(cv, names="Status", values="Model", hole=.55,
                     color_discrete_sequence=[ACCENT, "#f59e0b", "#cbd5e1"],
                     title="Cakupan model GSMArena di marketplace")
        show(fig, 360)
    with b:
        st.markdown("**Alur data (lineage)**")
        st.dataframe(pd.DataFrame({
            "Sumber": ["Tokopedia", "Shopee", "GSMArena", "YouTube"],
            "Database lokal": ["tokopedia_lokal.duckdb", "shopee_lokal.duckdb",
                               "gsmarena_lokal.duckdb", "youtube_lokal.duckdb"],
            "Di katalog bersama": ["lake.tokopedia", "lake.shopee", "lake.gsmarena", "lake.youtube"],
            "Dipakai di": ["fact_price", "fact_price", "dim_phone", "tab Komentar"],
        }), hide_index=True, use_container_width=True)
        st.markdown("**Lapisan lintas sumber:** `lake.analytics` → `dim_phone`, `map_listing`, "
                    "`fact_price`, `banding_harga`.")

    st.markdown("##### Riwayat snapshot & time travel (DuckLake)")
    try:
        con = get_con()
        snaps = con.sql("SELECT snapshot_id, snapshot_time, changes FROM lake.snapshots()").df()
        st.dataframe(snaps, hide_index=True, use_container_width=True)
        pilih = st.selectbox("Lihat jumlah baris fact_price pada snapshot",
                             snaps["snapshot_id"].tolist()[::-1])
        try:
            n = con.sql(f"SELECT count(*) AS n FROM lake.analytics.fact_price "
                        f"AT (VERSION => {int(pilih)})").fetchone()[0]
            st.metric(f"Baris fact_price di snapshot {int(pilih)}", num(n))
        except Exception:  # noqa: BLE001
            st.info("Tabel fact_price belum ada pada snapshot itu.")
    except Exception as e:  # noqa: BLE001
        st.info(f"Riwayat snapshot tidak tersedia: {e}")

st.markdown(
    '<div class="footer">Foto HP: GSMArena. Data harga dan komentar dikumpulkan dari '
    "Tokopedia, Shopee, dan YouTube.</div>",
    unsafe_allow_html=True,
)
