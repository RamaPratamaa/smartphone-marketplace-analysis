"""
Jalankan dari FOLDER UTAMA proyek:

    python SRC/build.py                        -> DuckLake (default), semua sumber + model
    python SRC/build.py --target duckdb        -> DuckDB lokal per sumber + DataBase/hp_model.duckdb
    python SRC/build.py --only shopee model    -> hanya tahap tertentu
                                                  (nama sumber di config.py, atau 'model')
"""
import argparse
import os
from pathlib import Path

import duckdb

import config

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)


def connect(target: str, db_path: str | None):
    if target == "ducklake":
        Path(config.LAKE_CATALOG).parent.mkdir(exist_ok=True)
        con = duckdb.connect()
        con.execute("INSTALL ducklake; LOAD ducklake;")
        con.execute(
            f"ATTACH 'ducklake:{config.LAKE_CATALOG}' AS lake "
            f"(DATA_PATH '{config.LAKE_DATA}')"
        )
        con.execute("USE lake")
        return con
    Path(db_path).parent.mkdir(exist_ok=True)
    return duckdb.connect(db_path)


def run_sql_dir(con, sql_dir: str):
    folder = Path(sql_dir)
    if not folder.exists():
        raise FileNotFoundError(f"Folder SQL tidak ditemukan: {folder}")
    for sql_file in sorted(folder.glob("*.sql")):
        print("  Menjalankan", sql_file.name)
        # Jalankan statement satu per satu. SELECT murni (pratinjau) dilewati supaya tidak ada
        # hasil query yang menggantung dan menahan transaksi (penting di DuckLake).
        for stmt in con.extract_statements(sql_file.read_text(encoding="utf-8")):
            if stmt.type == duckdb.StatementType.SELECT:
                continue
            try:
                con.execute(stmt.query)
            except Exception as e:
                raise RuntimeError(
                    f"Gagal di {sql_file}: {e}\n--- statement ---\n{stmt.query.strip()[:300]}"
                ) from e


def print_counts(con, tables):
    for t in tables:
        try:
            n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  - {t:<28}: {n} baris")
        except duckdb.CatalogException:
            print(f"  - {t:<28}: (tabel belum terbentuk)")


def copy_sources_into(con):
    """Target duckdb: salin tabel tiap sumber ke database model."""
    for name, cfg in config.SOURCES.items():
        if not Path(cfg["db"]).exists():
            print(f"  Peringatan: {cfg['db']} belum ada, sumber '{name}' dilewati.")
            continue
        alias = f"src_{name}"
        con.execute(f"ATTACH '{cfg['db']}' AS {alias} (READ_ONLY)")
        for table in cfg["tables"]:
            schema = table.split(".")[0]
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM {alias}.{table}")
        con.execute(f"DETACH {alias}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["ducklake", "duckdb"], default="ducklake")
    parser.add_argument("--only", nargs="+", help="nama sumber dan/atau 'model'")
    args = parser.parse_args()

    stages = list(config.SOURCES) + ["model"]
    if args.only:
        unknown = set(args.only) - set(stages)
        if unknown:
            parser.error(f"tahap tidak dikenal: {sorted(unknown)}; pilihan: {stages}")
        stages = [s for s in stages if s in args.only]

    for stage in stages:
        print(f"\n{'=' * 40}\nMEMPROSES: {stage.upper()}\n{'=' * 40}")
        if stage == "model":
            cfg = config.MODEL
            con = connect(args.target, config.MODEL_DB)
            if args.target == "duckdb":
                copy_sources_into(con)
        else:
            cfg = config.SOURCES[stage]
            con = connect(args.target, cfg["db"])

        run_sql_dir(con, cfg["sql_dir"])
        print(f"\nJumlah baris ({stage}):")
        print_counts(con, cfg["tables"])

        if args.target == "ducklake":
            print("\nRiwayat snapshot (5 terakhir):")
            for row in con.execute(
                "SELECT snapshot_id, snapshot_time, changes FROM lake.snapshots() "
                "ORDER BY snapshot_id DESC LIMIT 5"
            ).fetchall():
                print("  ", row)
        con.close()


if __name__ == "__main__":
    main()
