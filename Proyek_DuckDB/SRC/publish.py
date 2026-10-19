import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import LAKE_CATALOG, LAKE_DATA, SOURCES  # noqa: E402


def open_lake() -> duckdb.DuckDBPyConnection:
    Path(LAKE_CATALOG).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL ducklake; LOAD ducklake;")
    con.execute(f"ATTACH 'ducklake:{LAKE_CATALOG}' AS lake (DATA_PATH '{LAKE_DATA}')")
    return con


def publish(con: duckdb.DuckDBPyConnection) -> None:
    """Salin tabel tiap sumber ke lake.<sumber>.<tabel>. Aman dijalankan berulang."""
    for name, cfg in SOURCES.items():
        if not Path(cfg["db"]).exists():
            print(f"[{name}] {cfg['db']} belum ada, dilewati (jalankan build_local.py dulu)")
            continue
        alias = f"src_{name}"
        con.execute(f"ATTACH '{cfg['db']}' AS {alias} (READ_ONLY)")
        con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{name}")
        for src_table, dst_table in cfg["publish"]:
            con.execute(f"DROP TABLE IF EXISTS lake.{name}.{dst_table}")
            con.execute(f"CREATE TABLE lake.{name}.{dst_table} AS SELECT * FROM {alias}.{src_table}")
            n = con.sql(f"SELECT count(*) FROM lake.{name}.{dst_table}").fetchone()[0]
            print(f"[{name}] {src_table} -> lake.{name}.{dst_table} ({n} baris)")
        con.execute(f"DETACH {alias}")


if __name__ == "__main__":
    con = open_lake()
    con.execute("USE lake")
    publish(con)
    print("\nRiwayat snapshot katalog bersama:")
    print(con.sql("SELECT snapshot_id, snapshot_time, changes FROM lake.snapshots()"))
    con.close()
