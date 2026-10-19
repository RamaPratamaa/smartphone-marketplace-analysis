import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import SQL_LAKE_DIR  # noqa: E402
from publish import open_lake  # noqa: E402


def run_lake_sql(con: duckdb.DuckDBPyConnection) -> None:
    for f in sorted(Path(SQL_LAKE_DIR).glob("*.sql")):
        print(f"[lake] menjalankan {f.name}")
        con.execute(f.read_text(encoding="utf-8"))


def ringkasan(con: duckdb.DuckDBPyConnection) -> None:
    print("\nRingkasan:")
    for t in ["dim_phone", "map_listing", "fact_price", "banding_harga"]:
        n = con.sql(f"SELECT count(*) FROM lake.analytics.{t}").fetchone()[0]
        print(f"    lake.analytics.{t}: {n} baris")
    print(con.sql("""
        SELECT marketplace, count(*) AS listing_terpetakan,
               count(*) FILTER (WHERE layak) AS layak_dianalisis
        FROM lake.analytics.fact_price GROUP BY marketplace
    """))
    print(con.sql("""
        SELECT count(*) AS model_ada_di_kedua_marketplace,
               count(*) FILTER (WHERE cukup_data) AS dgn_data_cukup
        FROM lake.analytics.banding_harga
        WHERE listing_tokopedia > 0 AND listing_shopee > 0
    """))


if __name__ == "__main__":
    con = open_lake()
    con.execute("USE lake")
    run_lake_sql(con)
    ringkasan(con)
    print("\nRiwayat snapshot katalog bersama:")
    print(con.sql("SELECT snapshot_id, snapshot_time, changes FROM lake.snapshots()"))
    con.close()
