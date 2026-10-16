from pathlib import Path
import csv
import time
import duckdb

BASE = Path.cwd()

DATASETS = [
    "01_dunnhumby",
    "02_pakistan",
    "03_online_retail",
    "04_instacart",
    "05_hm",
]

con = duckdb.connect()

summary_rows = []
column_rows = []

for dataset in DATASETS:
    folder = BASE / dataset

    for path in sorted(folder.glob("*.csv")):
        print(f"검사 중: {dataset} / {path.name}")

        size_mb = path.stat().st_size / 1024 / 1024
        sql_path = path.resolve().as_posix().replace("'", "''")

        started = time.perf_counter()
        error = ""
        row_count = None
        schema = []

        try:
            # 컬럼명 + DuckDB 추정 타입
            schema = con.execute(
                f"""
                DESCRIBE
                SELECT *
                FROM read_csv_auto(
                    '{sql_path}',
                    header = true,
                    sample_size = 100000
                )
                """
            ).fetchall()

            # 행 수는 타입 변환 문제를 피하려고 모두 문자열로 읽어서 계산
            row_count = con.execute(
                f"""
                SELECT COUNT(*)
                FROM read_csv_auto(
                    '{sql_path}',
                    header = true,
                    all_varchar = true
                )
                """
            ).fetchone()[0]

        except Exception as e:
            error = str(e)

        elapsed = time.perf_counter() - started

        summary_rows.append({
            "dataset": dataset,
            "file": path.name,
            "size_mb": round(size_mb, 2),
            "row_count": row_count,
            "column_count": len(schema),
            "scan_seconds": round(elapsed, 2),
            "status": "OK" if not error else "ERROR",
            "error": error,
        })

        for i, row in enumerate(schema, start=1):
            column_rows.append({
                "dataset": dataset,
                "file": path.name,
                "column_order": i,
                "column_name": row[0],
                "duckdb_type": row[1],
            })


def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


write_csv(
    "audit_file_summary.csv",
    summary_rows,
    [
        "dataset",
        "file",
        "size_mb",
        "row_count",
        "column_count",
        "scan_seconds",
        "status",
        "error",
    ],
)

write_csv(
    "audit_columns.csv",
    column_rows,
    [
        "dataset",
        "file",
        "column_order",
        "column_name",
        "duckdb_type",
    ],
)

print("\n완료")
print("생성 파일:")
print(" - audit_file_summary.csv")
print(" - audit_columns.csv")