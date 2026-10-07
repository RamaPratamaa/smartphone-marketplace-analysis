import argparse
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import SOURCES  # noqa: E402


def build_source(name: str) -> None:
    cfg = SOURCES[name]
    sql_files = sorted(Path(cfg["sql_dir"]).glob("*.sql"))
    if not sql_files:
        print(f"[{name}] tidak ada file SQL di {cfg['sql_dir']}, dilewati")
        return
    Path(cfg["db"]).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(cfg["db"])
    for f in sql_files:
        print(f"[{name}] menjalankan {f.name}")
        con.execute(f.read_text(encoding="utf-8"))
    print(f"[{name}] selesai -> {cfg['db']}")
    for schema, table in con.sql(
        "SELECT schema_name, table_name FROM duckdb_tables() ORDER BY 1, 2"
    ).fetchall():
        n = con.sql(f"SELECT count(*) FROM {schema}.{table}").fetchone()[0]
        print(f"    {schema}.{table}: {n} baris")
    con.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=list(SOURCES), default=None)
    args = p.parse_args()
    for s in ([args.source] if args.source else SOURCES):
        build_source(s)
