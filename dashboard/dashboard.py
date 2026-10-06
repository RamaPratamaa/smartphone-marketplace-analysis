"""
Dashboard: Perbandingan Harga HP (Tokopedia vs Shopee) & Analisis Sentimen YouTube
Sumber data: data/lakehouse/lakehouse.ducklake (dibangun oleh notebook 04_build_ducklake.ipynb)

Jalankan dari folder repo (root), supaya path relatif "data/" benar:
    streamlit run app.py
"""
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Dashboard Smartphone — Data Warehouse", page_icon="📱", layout="wide")

LAKE_CATALOG = Path("data/lakehouse/lakehouse.ducklake")
LAKE_DATA_PATH = Path("data/lakehouse/files")


# ------------------------------------------------------------------
# Koneksi ke DuckLake (satu koneksi dipakai ulang sepanjang sesi)
# ------------------------------------------------------------------
@st.cache_resource
def get_connection():
    if not LAKE_CATALOG.exists():
        return None
    con = duckdb.connect(":memory:", read_only=False)
    con.execute("INSTALL ducklake")
    con.execute("LOAD ducklake")
    con.execute(f"ATTACH 'ducklake:{LAKE_CATALOG}' AS lake (READ_ONLY)")
    con.execute("USE lake")
    return con


def table_exists(con, name):
    try:
        con.execute(f"SELECT 1 FROM {name} LIMIT 0")
        return True
    except duckdb.Error:
        return False


@st.cache_data
def load_tables(_con):
    # _con (garis bawah) supaya Streamlit tidak mencoba meng-hash objek koneksi
    tables = {}
    for name in ["dim_brand", "dim_phone", "fact_sales", "dim_platform", "mart_price_comparison",
                "mart_price_stats", "mart_sentiment_summary", "mart_sentiment_vs_price"]:
        tables[name] = _con.execute(f"SELECT * FROM {name}").df() if table_exists(_con, name) else pd.DataFrame()
    return tables


# ------------------------------------------------------------------
# Muat data
# ------------------------------------------------------------------
con = get_connection()

if con is None:
    st.error(
        f"Belum ada data. File **{LAKE_CATALOG}** tidak ditemukan.\n\n"
        "Jalankan notebook scraping (01–03) lalu `04_build_ducklake.ipynb` terlebih dahulu, "
        "dan pastikan dashboard ini dijalankan dari folder repo (root), bukan dari dalam folder lain."
    )
    st.stop()

data = load_tables(con)
dim_phone, dim_brand, fact_sales = data["dim_phone"], data["dim_brand"], data["fact_sales"]
price_compare = data["mart_price_comparison"]
sentiment_vs_price = data["mart_sentiment_vs_price"]

if dim_phone.empty or fact_sales.empty:
    st.warning("Database gold ditemukan tetapi masih kosong. Jalankan ulang notebook `04_build_ducklake.ipynb`.")
    st.stop()

phones = dim_phone.merge(dim_brand, on="brand_id")
HAS_PRICE_COMPARE = not price_compare.empty
HAS_SENTIMENT = not sentiment_vs_price.empty


# ------------------------------------------------------------------
# Sidebar: filter
# ------------------------------------------------------------------
st.sidebar.header("🔍 Filter")

all_brands = sorted(phones["brand_name"].unique())
sel_brands = st.sidebar.multiselect("Brand", all_brands, default=all_brands)

year_min, year_max = int(phones["release_year"].min()), int(phones["release_year"].max())
if year_min == year_max:
    sel_years = (year_min, year_max)
    st.sidebar.caption(f"Tahun rilis: {year_min} (hanya satu tahun tersedia)")
else:
    sel_years = st.sidebar.slider("Tahun rilis", year_min, year_max, (year_min, year_max))

if HAS_PRICE_COMPARE:
    price_min = int(price_compare[["Tokopedia", "Shopee"]].min().min())
    price_max = int(price_compare[["Tokopedia", "Shopee"]].max().max())
    if price_min == price_max:
        sel_price = (price_min, price_max)
    else:
        sel_price = st.sidebar.slider("Rentang harga (Rp)", price_min, price_max, (price_min, price_max),
                                      format="Rp%d")
else:
    sel_price = None

phones_f = phones[phones["brand_name"].isin(sel_brands)
                  & phones["release_year"].between(*sel_years)]

if HAS_PRICE_COMPARE:
    pc_f = price_compare[price_compare["phone_name"].isin(phones_f["phone_name"])]
    if sel_price:
        pc_f = pc_f[pc_f["Tokopedia"].between(*sel_price) | pc_f["Shopee"].between(*sel_price)]
else:
    pc_f = pd.DataFrame()


# ------------------------------------------------------------------
# Ringkasan atas
# ------------------------------------------------------------------
st.title("📱 Dashboard Perbandingan Harga & Persepsi Publik Smartphone")
st.caption("Sumber: GSMArena (spesifikasi) · Tokopedia & Shopee (harga) · YouTube (sentimen, jika tersedia)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("HP di database", f"{len(dim_phone):,}")
c2.metric("HP dibandingkan harganya", f"{len(pc_f):,}" if HAS_PRICE_COMPARE else "–")
c3.metric("Total listing (setelah filter)", f"{len(fact_sales[fact_sales['phone_id'].isin(phones_f['phone_id'])]):,}")
if HAS_PRICE_COMPARE and not pc_f.empty:
    avg_diff = pc_f["selisih_pct"].mean()
    c4.metric("Rata-rata selisih Shopee vs Tokopedia", f"{avg_diff:+.1f}%")
else:
    c4.metric("Rata-rata selisih harga", "–")

if not HAS_PRICE_COMPARE:
    st.info("Perbandingan harga Tokopedia vs Shopee belum tersedia — kemungkinan `data/shopee.duckdb` belum "
            "ada saat `04_build_ducklake.ipynb` terakhir dijalankan. Jalankan notebook Shopee, lalu build_ducklake ulang.")

st.divider()


# ------------------------------------------------------------------
# Perbandingan harga
# ------------------------------------------------------------------
if HAS_PRICE_COMPARE:
    st.header("💰 Perbandingan Harga: Tokopedia vs Shopee")

    if pc_f.empty:
        st.warning("Tidak ada HP yang cocok dengan filter saat ini.")
    else:
        tab1, tab2 = st.tabs(["Tabel", "Grafik"])
        with tab1:
            show = pc_f[["phone_name", "Tokopedia", "Shopee", "selisih_rp", "selisih_pct", "lebih_murah"]] \
                .sort_values("selisih_pct").rename(columns={
                    "phone_name": "HP", "selisih_rp": "Selisih (Rp)", "selisih_pct": "Selisih (%)",
                    "lebih_murah": "Lebih murah di"})
            st.dataframe(show, use_container_width=True, hide_index=True,
                        column_config={"Tokopedia": st.column_config.NumberColumn(format="Rp %d"),
                                       "Shopee": st.column_config.NumberColumn(format="Rp %d"),
                                       "Selisih (Rp)": st.column_config.NumberColumn(format="Rp %d")})
        with tab2:
            top = pc_f.sort_values("Tokopedia", ascending=False).head(20)
            melted = top.melt(id_vars="phone_name", value_vars=["Tokopedia", "Shopee"],
                              var_name="Platform", value_name="Harga")
            fig = px.bar(melted, x="phone_name", y="Harga", color="Platform", barmode="group",
                        labels={"phone_name": "HP", "Harga": "Harga (Rp)"},
                        title="Harga per HP (20 HP dengan harga tertinggi)")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()


# ------------------------------------------------------------------
# Sentimen YouTube
# ------------------------------------------------------------------
if HAS_SENTIMENT:
    sv_f = sentiment_vs_price[sentiment_vs_price["phone_name"].isin(phones_f["phone_name"])]
    st.header("💬 Sentimen Komentar YouTube")

    if sv_f.empty:
        st.warning("Tidak ada HP yang cocok dengan filter saat ini.")
    else:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader("Harga vs Sentimen Negatif")
            st.caption("HP di kanan-atas: harga tinggi tapi sentimen negatif juga tinggi — kandidat yang "
                      "mungkin perlu perhatian branding/iklan. HP di kiri-bawah: sentimen positif dominan.")
            price_col = "Tokopedia" if "Tokopedia" in sv_f.columns else None
            if price_col:
                fig2 = px.scatter(sv_f, x=price_col, y="pct_negative", size="n_comments", color="dominant_sentiment",
                                  hover_name="phone_name", labels={price_col: "Harga Tokopedia (Rp)",
                                                                   "pct_negative": "% Komentar Negatif"})
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.dataframe(sv_f[["phone_name", "pct_positive", "pct_neutral", "pct_negative", "n_comments"]],
                            use_container_width=True, hide_index=True)
        with col2:
            st.subheader("Ringkasan")
            st.dataframe(
                sv_f[["phone_name", "pct_positive", "pct_negative", "indikasi_branding"]]
                .rename(columns={"phone_name": "HP", "pct_positive": "% Positif", "pct_negative": "% Negatif",
                                 "indikasi_branding": "Indikasi"})
                .sort_values("% Negatif", ascending=False),
                use_container_width=True, hide_index=True)
        st.caption("⚠️ `indikasi_branding` adalah aturan sederhana (ambang rasio 1,5x), bukan kesimpulan statistik "
                  "yang ketat — lihat catatan keterbatasan di notebook YouTube.")
    st.divider()
else:
    st.info("💬 Data sentimen YouTube belum tersedia. Jalankan notebook scraping YouTube lalu `04_build_ducklake.ipynb` "
            "ulang untuk mengaktifkan bagian ini.")
    st.divider()


# ------------------------------------------------------------------
# Detail per HP
# ------------------------------------------------------------------
st.header("🔎 Detail per HP")
if phones_f.empty:
    st.warning("Tidak ada HP yang cocok dengan filter saat ini.")
else:
    picked = st.selectbox("Pilih HP", sorted(phones_f["phone_name"]))
    prow = phones_f[phones_f["phone_name"] == picked].iloc[0]

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Chipset", prow["chipset"])
    d2.metric("RAM", f"{prow['ram_gb']:g} GB" if pd.notna(prow["ram_gb"]) else "–")
    d3.metric("Storage", f"{prow['storage_gb']:g} GB" if pd.notna(prow["storage_gb"]) else "–")
    d4.metric("Baterai", f"{prow['battery_mah']:g} mAh" if pd.notna(prow["battery_mah"]) else "–")

    if HAS_PRICE_COMPARE:
        prow_price = price_compare[price_compare["phone_name"] == picked]
        if not prow_price.empty:
            pr = prow_price.iloc[0]
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("Harga Tokopedia", f"Rp {pr['Tokopedia']:,.0f}")
            pc2.metric("Harga Shopee", f"Rp {pr['Shopee']:,.0f}")
            pc3.metric("Lebih murah di", pr["lebih_murah"])

    if HAS_SENTIMENT:
        srow = sentiment_vs_price[sentiment_vs_price["phone_name"] == picked]
        if not srow.empty:
            s = srow.iloc[0]
            st.write(f"**Sentimen** ({int(s['n_comments'])} komentar): "
                    f"{s['pct_positive']:.0f}% positif · {s['pct_neutral']:.0f}% netral · {s['pct_negative']:.0f}% negatif "
                    f"— *{s['indikasi_branding']}*")

st.caption("Dashboard ini membaca dari data/lakehouse/lakehouse.ducklake — jalankan ulang notebook scraping & "
          "build_ducklake untuk memperbarui data, lalu refresh halaman ini.")
