"""
Menambah / memperbarui tab "Lokasi Penjual" (penjualan per wilayah) di app/app.py.

Jalankan dari FOLDER UTAMA proyek (yang berisi folder app/):
    python tambah_tab_lokasi.py
atau sebut path file-nya (mis. dari dalam folder app):
    python tambah_tab_lokasi.py app.py

Bisa dipakai di dua keadaan:
  - app.py belum punya tab Lokasi Penjual  -> tab ditambahkan
  - app.py sudah punya versi lama tab ini  -> tab diperbarui (ditambah penjualan per wilayah)
Aman: file asli dicadangkan ke app.py.bak; bila ada bagian yang tidak cocok, skrip berhenti
TANPA mengubah apa pun.
"""
import shutil
import sys
from pathlib import Path

target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("app/app.py")
if not target.exists():
    sys.exit(f"File tidak ditemukan: {target}\nJalankan dari folder utama proyek, atau sebut path-nya.")

raw = target.read_bytes().decode("utf-8")
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")

VERSI = "# versi: terjual-per-wilayah"
if VERSI in s:
    sys.exit("Tab Lokasi Penjual sudah versi terbaru (ada penjualan per wilayah). Tidak ada yang diubah.")

MULAI = "# ============================ TAB 6: LOKASI PENJUAL ============================"
sudah_ada = "TAB 6: LOKASI PENJUAL" in s
if '"🧪 Data & Kualitas"' in s:
    GAYA = "lama"      # dashboard dengan tab ber-emoji
    LIST_LAMA = '    "🔧 Spesifikasi vs Harga", "💬 Suara Komentar", "🧪 Data & Kualitas",'
    LIST_BARU = '    "🔧 Spesifikasi vs Harga", "💬 Suara Komentar", "📍 Lokasi Penjual", "🧪 Data & Kualitas",'
    HDR_DATA, AKHIR_LAMA = "TAB 6: DATA & KUALITAS", "# ============================ TAB 7: DATA & KUALITAS ============================"
    TOKEN_KOMENTAR = "tab Suara Komentar"
elif '"Kualitas Data"' in s:
    GAYA = "baru"      # dashboard dengan galeri HP
    LIST_LAMA = '    "Spesifikasi vs Harga", "Komentar", "Kualitas Data",'
    LIST_BARU = '    "Spesifikasi vs Harga", "Komentar", "Lokasi Penjual", "Kualitas Data",'
    HDR_DATA, AKHIR_LAMA = "TAB 6: KUALITAS DATA", "# ============================ TAB 7: KUALITAS DATA ============================"
    TOKEN_KOMENTAR = "tab Komentar"
else:
    sys.exit("Bentuk daftar tab di file ini tidak dikenali, file TIDAK diubah.\nKirim app.py Anda supaya skrip ini disesuaikan.")
print(f"Gaya dashboard terdeteksi: {GAYA}")
gagal = []


def ganti(nama, lama, baru, wajib=True):
    global s
    if s.count(lama) != 1:
        if wajib:
            gagal.append(nama)
        print(f"  {'GAGAL  ' if wajib else 'dilewati'}: {nama} (ditemukan {s.count(lama)}x, harusnya 1x)")
        return
    s = s.replace(lama, baru)
    print(f"  ok      : {nama}")


TAB_BARU = '''# ============================ TAB 6: LOKASI PENJUAL ============================
# versi: terjual-per-wilayah
with tabs[5], guard():
    _ACC, _BLUE = globals().get("ACCENT", "#0E7C86"), globals().get("BLUE", "#3E6FB0")
    wil = D["wil"]
    if wil is None or base["wilayah_id"].notna().sum() == 0:
        st.info("Data lokasi belum ada pada filter ini / belum ada di katalog. Pastikan data wilayah "
                "sudah dibangun: `python SRC/build_local.py` → `python SRC/publish.py` "
                "→ `python SRC/build_lake.py`.")
    else:
        bw = base.dropna(subset=["wilayah_id"]).merge(wil, on="wilayah_id", how="left")
        bw["provinsi"] = bw["provinsi"].replace({"Daerah Khusus Ibukota Jakarta": "DKI Jakarta"})
        bw["nama"] = bw["nama"].str.replace(" Administrasi", "", regex=False)

        # toko dengan penjualan terbesar (dihitung dari seluruh data ber-lokasi)
        top_toko = bw.groupby("seller_name")["terjual"].sum().nlargest(5)
        total_all = float(bw["terjual"].sum())
        share_top5 = top_toko.sum() / total_all * 100 if total_all > 0 else 0.0

        sembunyi = st.checkbox("Sembunyikan 5 toko dengan penjualan terbesar", value=False,
                               help="Toko resmi besar sering mendominasi angka satu wilayah. "
                                    "Centang untuk melihat sebaran tanpa mereka.")
        if sembunyi:
            bw = bw[~bw["seller_name"].isin(top_toko.index)].copy()
        if bw.empty:
            st.info("Tidak ada data tersisa setelah toko teratas disembunyikan.")
        else:
            prov = (bw.groupby("provinsi")
                    .agg(terjual=("terjual", "sum"), listing=("harga", "size"),
                         toko=("seller_name", "nunique"), kab_kota=("nama", "nunique"))
                    .reset_index().sort_values("terjual", ascending=False))
            tot = float(prov["terjual"].sum())
            share = prov["terjual"] / tot * 100 if tot > 0 else prov["terjual"] * 0

            c = st.columns(4)
            kpi(c[0], "Total terjual (toko ber-lokasi)", num(tot), "terlapor di label marketplace")
            kpi(c[1], "Kabupaten/kota", num(bw["nama"].nunique()), f"{bw['provinsi'].nunique()} provinsi")
            kpi(c[2], "Provinsi teratas", prov.iloc[0]["provinsi"], f"{share.iloc[0]:.0f}% dari total terjual")
            kpi(c[3], "Konsentrasi 5 toko teratas", f"{share_top5:.0f}%", "dari total terjual (semua data)")

            top3 = prov.head(3)["provinsi"].tolist()
            insight(f"**{top3[0]}** mencatat {share.iloc[0]:.0f}% penjualan terlapor; tiga provinsi teratas "
                    f"({', '.join(top3)}) menyumbang **{share.head(3).sum():.0f}%**. Lima toko terbesar "
                    f"menguasai **{share_top5:.0f}%** penjualan, jadi angka per wilayah sangat dipengaruhi "
                    "lokasi toko resmi/besar, bukan semata permintaan di daerah itu.")

            a, b = st.columns(2)
            with a:
                t = prov.head(10).sort_values("terjual")
                fig = px.bar(t, x="terjual", y="provinsi", orientation="h",
                             color_discrete_sequence=[_ACC], hover_data={"listing": True, "toko": True},
                             title="Produk terjual per provinsi (lokasi toko)")
                fig.update_layout(xaxis_title="Unit terjual (terlapor)", yaxis_title="")
                show(fig, 420)
            with b:
                p6 = prov.head(6)["provinsi"].tolist()
                top_brand6 = bw.groupby("brand")["terjual"].sum().nlargest(6).index
                mb = bw[bw["provinsi"].isin(p6)].copy()
                mb["merek"] = np.where(mb["brand"].isin(top_brand6), mb["brand"], "Lainnya")
                mb = mb.groupby(["provinsi", "merek"], as_index=False)["terjual"].sum()
                fig = px.bar(mb, x="terjual", y="provinsi", color="merek", orientation="h",
                             category_orders={"provinsi": p6[::-1]},
                             title="Merek yang terjual di 6 provinsi teratas")
                fig.update_layout(barmode="stack", xaxis_title="Unit terjual (terlapor)", yaxis_title="")
                show(fig, 420)

            kab = (bw.groupby(["nama", "provinsi"], as_index=False)
                   .agg(terjual=("terjual", "sum"), listing=("harga", "size"),
                        toko=("seller_name", "nunique"), harga_median=("harga", "median"),
                        penduduk=("penduduk", "first"))
                   .sort_values("terjual", ascending=False))
            kab["terjual_per_juta"] = kab["terjual"] / kab["penduduk"] * 1e6

            a, b = st.columns(2)
            with a:
                t = kab.head(12).sort_values("terjual")
                fig = px.bar(t, x="terjual", y="nama", orientation="h", color_discrete_sequence=[_BLUE],
                             hover_data={"provinsi": True, "toko": True},
                             title="Produk terjual per kabupaten/kota (12 teratas)")
                fig.update_layout(xaxis_title="Unit terjual (terlapor)", yaxis_title="")
                show(fig, 420)
            with b:
                pilih = st.selectbox("Lihat model terlaris di provinsi", prov["provinsi"].tolist(),
                                     key="prov_model")
                mp = (bw[bw["provinsi"] == pilih].groupby(["phone_name", "brand"], as_index=False)
                      .agg(terjual=("terjual", "sum"), listing=("harga", "size"))
                      .nlargest(8, "terjual").sort_values("terjual"))
                fig = px.bar(mp, x="terjual", y="phone_name", orientation="h", color="brand",
                             hover_data={"listing": True},
                             title=f"Model terlaris di {pilih}")
                fig.update_layout(xaxis_title="Unit terjual (terlapor)", yaxis_title="")
                show(fig, 380)

            st.markdown("##### Kabupaten/kota")
            st.dataframe(
                kab[["nama", "provinsi", "terjual", "listing", "toko", "harga_median", "penduduk",
                     "terjual_per_juta"]],
                hide_index=True, use_container_width=True,
                column_config={
                    "nama": "Kabupaten/kota", "provinsi": "Provinsi",
                    "terjual": st.column_config.NumberColumn("Terjual (terlapor)", format="%d"),
                    "listing": st.column_config.NumberColumn("Listing", format="%d"),
                    "toko": st.column_config.NumberColumn("Jumlah toko", format="%d"),
                    "harga_median": st.column_config.NumberColumn("Median harga", format="Rp %d"),
                    "penduduk": st.column_config.NumberColumn("Penduduk", format="%d"),
                    "terjual_per_juta": st.column_config.NumberColumn("Terjual per 1 juta penduduk",
                                                                      format="%.0f"),
                },
            )
            warn("**Cara membaca.** Lokasi adalah **lokasi toko penjual**, bukan lokasi pembeli, jadi ini "
                 "menunjukkan dari wilayah mana produk dijual, bukan di mana permintaannya. 'Terjual' adalah "
                 "angka label marketplace (kumulatif per listing, batas bawah: '1rb+' dihitung 1.000), dan "
                 "listing tanpa angka terjual tidak ikut dijumlah. Toko besar/resmi dapat mendominasi satu "
                 "wilayah, gunakan opsi sembunyikan toko teratas untuk membandingkan.")

'''

# ---- bagian yang selalu ada pada query: ikut bawa seller_name ----
if sudah_ada:
    print("Terdeteksi versi lama tab Lokasi Penjual -> diperbarui.")
    a, b = s.find(MULAI), s.find(AKHIR_LAMA)
    if a == -1 or b == -1 or b < a:
        sys.exit("Penanda tab lama tidak ditemukan, file TIDAK diubah.\nKirim app.py Anda supaya skrip ini disesuaikan.")
    s = s[:a] + TAB_BARU + s[b:]
    print("  ok      : isi tab diganti")
    if "f.seller_name" not in s:
        ganti("seller_name di query", "f.layak, f.pasti, {wil_sel}, p.brand",
              "f.layak, f.pasti, f.seller_name, {wil_sel}, p.brand")
else:
    print("Tab belum ada -> ditambahkan.")
    ganti("query fact_price", '''    d["fact"] = q(
        """
        SELECT f.phone_id, f.marketplace, f.harga, f.harga_asli, f.rating, f.terjual,
               f.layak, f.pasti, p.brand, p.phone_name, p.ram_max_gb, p.storage_max_gb,
               p.battery_mah, p.release_year
        FROM lake.analytics.fact_price f
        JOIN lake.analytics.dim_phone p USING (phone_id)
        """
    )
    for col in ["harga", "harga_asli", "rating", "terjual", "ram_max_gb", "storage_max_gb",
                "battery_mah", "release_year"]:''', '''    kolom_fact = [r[0] for r in con.execute("DESCRIBE lake.analytics.fact_price").fetchall()]
    wil_sel = "f.wilayah_id" if "wilayah_id" in kolom_fact else "CAST(NULL AS INTEGER) AS wilayah_id"
    d["fact"] = q(
        f"""
        SELECT f.phone_id, f.marketplace, f.harga, f.harga_asli, f.rating, f.terjual,
               f.layak, f.pasti, f.seller_name, {wil_sel}, p.brand, p.phone_name, p.ram_max_gb,
               p.storage_max_gb, p.battery_mah, p.release_year
        FROM lake.analytics.fact_price f
        JOIN lake.analytics.dim_phone p USING (phone_id)
        """
    )
    for col in ["harga", "harga_asli", "rating", "terjual", "ram_max_gb", "storage_max_gb",
                "battery_mah", "release_year", "wilayah_id"]:''')
    ganti("muat dim_wilayah", '''    d["yt"] = q(
        """
        SELECT channel, komentar, like_count, tanggal''', '''    try:
        d["wil"] = q("SELECT wilayah_id, provinsi, nama, jenis, penduduk "
                     "FROM lake.analytics.dim_wilayah")
        for col in ["wilayah_id", "penduduk"]:
            d["wil"][col] = pd.to_numeric(d["wil"][col], errors="coerce").astype("float64")
    except Exception:  # noqa: BLE001  (katalog belum punya dim_wilayah)
        d["wil"] = None
    d["yt"] = q(
        """
        SELECT channel, komentar, like_count, tanggal''')
    ganti("daftar tab", LIST_LAMA, LIST_BARU)
    ganti("indeks tab Kualitas Data", "with tabs[5], guard():", "with tabs[6], guard():")
    ganti("sisipkan tab baru",
          "# ============================ " + HDR_DATA + " ============================",
          TAB_BARU + AKHIR_LAMA)
    ganti("tabel lineage", '''            "Sumber": ["Tokopedia", "Shopee", "GSMArena", "YouTube"],
            "Database lokal": ["tokopedia_lokal.duckdb", "shopee_lokal.duckdb",
                               "gsmarena_lokal.duckdb", "youtube_lokal.duckdb"],
            "Di katalog bersama": ["lake.tokopedia", "lake.shopee", "lake.gsmarena", "lake.youtube"],
            "Dipakai di": ["fact_price", "fact_price", "dim_phone", "''' + TOKEN_KOMENTAR + '''"],''',
          '''            "Sumber": ["Tokopedia", "Shopee", "GSMArena", "YouTube", "Wilayah"],
            "Database lokal": ["tokopedia_lokal.duckdb", "shopee_lokal.duckdb",
                               "gsmarena_lokal.duckdb", "youtube_lokal.duckdb",
                               "wilayah_lokal.duckdb"],
            "Di katalog bersama": ["lake.tokopedia", "lake.shopee", "lake.gsmarena", "lake.youtube",
                                   "lake.wilayah"],
            "Dipakai di": ["fact_price", "fact_price", "dim_phone", "''' + TOKEN_KOMENTAR + '''",
                           "dim_wilayah (tab Lokasi Penjual)"],''', wajib=False)
    ganti("keterangan lapisan analytics", '''"`fact_price`, `banding_harga`.")''',
          '''"`dim_wilayah`, `map_wilayah`, `fact_price`, `banding_harga`.")''', wajib=False)
    # kompatibilitas DuckDB 2.0 (indentasi berbeda antar gaya dashboard)
    for ind in ("            ", "                "):
        lama = (ind + 'n = con.sql(f"SELECT count(*) AS n FROM lake.analytics.fact_price "\n'
                + ind + " " * 12 + 'f"AT (VERSION => {int(pilih)})").fetchone()[0]')
        baru = (ind + 'n = con.execute(f"SELECT count(*) AS n FROM lake.analytics.fact_price "\n'
                + ind + " " * 16 + 'f"AT (VERSION => {int(pilih)})").fetchall()[0][0]')
        if s.count(lama) == 1:
            ganti("time travel (DuckDB 2.0)", lama, baru, wajib=False)
            break

if gagal:
    sys.exit("\nDIBATALKAN, file TIDAK diubah. Bagian wajib yang tidak cocok: " + ", ".join(gagal)
             + "\nKirim app.py terbaru Anda supaya skrip ini disesuaikan.")

shutil.copyfile(target, str(target) + ".bak")
out = s.replace("\n", "\r\n") if crlf else s
target.write_bytes(out.encode("utf-8"))
print(f"\nSELESAI. Cadangan: {target}.bak  |  Jalankan: streamlit run {target}")