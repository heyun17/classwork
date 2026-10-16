from pathlib import Path
import csv
import time
import duckdb

BASE = Path.cwd()
OUT = BASE / "audit_final_3way.csv"

con = duckdb.connect()
con.execute("PRAGMA threads=4")

FIELDS = [
    "dataset",
    "grain",
    "fact_files",
    "fact_size_gb",
    "fact_rows",
    "secondary_fact_rows",
    "period_min",
    "period_max",

    "product_count",
    "customer_count",
    "location_count",
    "order_or_basket_count",
    "session_count",

    "quantity_source",
    "quantity_min",
    "quantity_max",
    "negative_quantity_rows",

    "price_source",
    "price_min",
    "price_max",

    "return_cancel_source",
    "return_cancel_rows",

    "purchase_rows",

    "product_master",
    "location_master",
    "customer_master",

    "large_join_possible",
    "date_partition_possible",

    "scan_seconds",
    "status",
    "error",
]

results = []


def sql_path(path):
    return (
        path.resolve()
        .as_posix()
        .replace("'", "''")
    )


def size_gb(paths):
    total = sum(path.stat().st_size for path in paths)
    return round(total / 1024**3, 3)


def blank_row(dataset):
    row = {field: None for field in FIELDS}
    row["dataset"] = dataset
    return row


def save():
    with open(
        OUT,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS
        )
        writer.writeheader()
        writer.writerows(results)


# ============================================================
# 1. DUNNHUMBY
# ============================================================

print("\n" + "=" * 72)
print("1/3 Dunnhumby 최종 검사")
start = time.perf_counter()

row = blank_row("Dunnhumby")

try:
    tx_file = BASE / "01_dunnhumby" / "transaction_data.csv"
    causal_file = BASE / "01_dunnhumby" / "causal_data.csv"
    product_file = BASE / "01_dunnhumby" / "product.csv"

    tx = sql_path(tx_file)
    causal = sql_path(causal_file)
    product = sql_path(product_file)

    stats = con.execute(
        f"""
        SELECT
            COUNT(*) AS fact_rows,

            MIN(DAY) AS period_min,
            MAX(DAY) AS period_max,

            COUNT(DISTINCT PRODUCT_ID)
                AS product_count,

            COUNT(DISTINCT household_key)
                AS customer_count,

            COUNT(DISTINCT STORE_ID)
                AS location_count,

            COUNT(DISTINCT BASKET_ID)
                AS basket_count,

            MIN(QUANTITY)
                AS quantity_min,

            MAX(QUANTITY)
                AS quantity_max,

            COUNT(*) FILTER (
                WHERE QUANTITY < 0
            ) AS negative_quantity_rows,

            MIN(SALES_VALUE)
                AS price_min,

            MAX(SALES_VALUE)
                AS price_max

        FROM read_csv_auto(
            '{tx}',
            header=true
        )
        """
    ).fetchone()

    causal_rows = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{causal}',
            header=true
        )
        """
    ).fetchone()[0]

    row.update({
        "grain":
            "purchase line / basket-product transaction",
        "fact_files": 2,
        "fact_size_gb":
            size_gb([tx_file, causal_file]),
        "fact_rows": stats[0],
        "secondary_fact_rows": causal_rows,

        "period_min": stats[1],
        "period_max": stats[2],

        "product_count": stats[3],
        "customer_count": stats[4],
        "location_count": stats[5],
        "order_or_basket_count": stats[6],
        "session_count": None,

        "quantity_source": "ORIGINAL",
        "quantity_min": stats[7],
        "quantity_max": stats[8],
        "negative_quantity_rows": stats[9],

        "price_source":
            "ORIGINAL (SALES_VALUE=line sales value)",
        "price_min": stats[10],
        "price_max": stats[11],

        "return_cancel_source": "NOT EXPLICIT",
        "return_cancel_rows": None,

        "purchase_rows": stats[0],

        "product_master": "YES",
        "location_master":
            "NO (STORE_ID exists, separate master absent)",
        "customer_master":
            "PARTIAL (hh_demographic)",

        "large_join_possible":
            "YES: transaction + causal + product",

        "date_partition_possible":
            "YES: DAY / WEEK_NO",

        "status": "OK",
    })

except Exception as e:
    row["status"] = "ERROR"
    row["error"] = str(e)

row["scan_seconds"] = round(
    time.perf_counter() - start,
    2
)

results.append(row)
save()

print(
    f"완료: {row['scan_seconds']}초 "
    f"[{row['status']}]"
)


# ============================================================
# 2. FAVORITA
# ============================================================

print("\n" + "=" * 72)
print("2/3 Favorita 최종 검사")
start = time.perf_counter()

row = blank_row("Favorita")

try:
    train_file = BASE / "06_favorita" / "train.csv"
    items_file = BASE / "06_favorita" / "items.csv"
    stores_file = BASE / "06_favorita" / "stores.csv"
    trans_file = BASE / "06_favorita" / "transactions.csv"

    train = sql_path(train_file)
    items = sql_path(items_file)
    stores = sql_path(stores_file)
    trans = sql_path(trans_file)

    stats = con.execute(
        f"""
        SELECT
            COUNT(*) AS fact_rows,

            MIN(date) AS period_min,
            MAX(date) AS period_max,

            COUNT(DISTINCT item_nbr)
                AS product_count,

            COUNT(DISTINCT store_nbr)
                AS location_count,

            MIN(unit_sales)
                AS quantity_min,

            MAX(unit_sales)
                AS quantity_max,

            COUNT(*) FILTER (
                WHERE unit_sales < 0
            ) AS negative_quantity_rows

        FROM read_csv_auto(
            '{train}',
            header=true
        )
        """
    ).fetchone()

    item_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{items}',
            header=true
        )
        """
    ).fetchone()[0]

    store_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{stores}',
            header=true
        )
        """
    ).fetchone()[0]

    transaction_stats = con.execute(
        f"""
        SELECT
            COUNT(*) AS rows,
            SUM(transactions) AS transaction_total
        FROM read_csv_auto(
            '{trans}',
            header=true
        )
        """
    ).fetchone()

    row.update({
        "grain":
            "date-store-item aggregated sales",
        "fact_files": 1,
        "fact_size_gb":
            size_gb([train_file]),
        "fact_rows": stats[0],
        "secondary_fact_rows":
            transaction_stats[0],

        "period_min": stats[1],
        "period_max": stats[2],

        "product_count": stats[3],
        "customer_count": None,
        "location_count": stats[4],
        "order_or_basket_count": None,
        "session_count": None,

        "quantity_source": "ORIGINAL",
        "quantity_min": stats[5],
        "quantity_max": stats[6],
        "negative_quantity_rows": stats[7],

        "price_source": "ABSENT",
        "price_min": None,
        "price_max": None,

        "return_cancel_source":
            "ORIGINAL: negative unit_sales",
        "return_cancel_rows": stats[7],

        "purchase_rows": None,

        "product_master":
            f"YES ({item_count} rows)",

        "location_master":
            f"YES ({store_count} rows)",

        "customer_master": "NO",

        "large_join_possible":
            "YES: train + items + stores + transactions",

        "date_partition_possible":
            "YES: actual calendar date",

        "status": "OK",
    })

except Exception as e:
    row["status"] = "ERROR"
    row["error"] = str(e)

row["scan_seconds"] = round(
    time.perf_counter() - start,
    2
)

results.append(row)
save()

print(
    f"완료: {row['scan_seconds']}초 "
    f"[{row['status']}]"
)


# ============================================================
# 3. REES46
# ============================================================

print("\n" + "=" * 72)
print("3/3 REES46 최종 검사")
print("※ 약 14.7GB 전체 스캔이므로 가장 오래 걸릴 수 있음.")
start = time.perf_counter()

row = blank_row("REES46")

try:
    oct_file = BASE / "07_rees46" / "2019-Oct.csv"
    nov_file = BASE / "07_rees46" / "2019-Nov.csv"

    oct_path = sql_path(oct_file)
    nov_path = sql_path(nov_file)

    stats = con.execute(
        f"""
        WITH events AS (

            SELECT *
            FROM read_csv_auto(
                '{oct_path}',
                header=true
            )

            UNION ALL

            SELECT *
            FROM read_csv_auto(
                '{nov_path}',
                header=true
            )
        ),

        prepared AS (
            SELECT
                *,

                TRY_CAST(
                    SUBSTR(
                        CAST(event_time AS VARCHAR),
                        1,
                        10
                    )
                    AS DATE
                ) AS event_date

            FROM events
        )

        SELECT
            COUNT(*) AS fact_rows,

            MIN(event_date)
                AS period_min,

            MAX(event_date)
                AS period_max,

            COUNT(DISTINCT product_id)
                AS product_count,

            COUNT(DISTINCT user_id)
                AS customer_count,

            COUNT(DISTINCT user_session)
                AS session_count,

            MIN(price)
                AS price_min,

            MAX(price)
                AS price_max,

            COUNT(*) FILTER (
                WHERE event_type = 'purchase'
            ) AS purchase_rows,

            COUNT(DISTINCT user_session)
                FILTER (
                    WHERE event_type = 'purchase'
                ) AS purchase_sessions,

            COUNT(*) FILTER (
                WHERE event_type = 'view'
            ) AS view_rows,

            COUNT(*) FILTER (
                WHERE event_type = 'cart'
            ) AS cart_rows,

            COUNT(*) FILTER (
                WHERE event_type = 'remove_from_cart'
            ) AS remove_cart_rows

        FROM prepared
        """
    ).fetchone()

    row.update({
        "grain":
            "user-product behavior event",

        "fact_files": 2,

        "fact_size_gb":
            size_gb([oct_file, nov_file]),

        "fact_rows": stats[0],
        "secondary_fact_rows": None,

        "period_min": stats[1],
        "period_max": stats[2],

        "product_count": stats[3],
        "customer_count": stats[4],
        "location_count": None,

        "order_or_basket_count":
            stats[9],

        "session_count": stats[5],

        "quantity_source": "ABSENT",
        "quantity_min": None,
        "quantity_max": None,
        "negative_quantity_rows": None,

        "price_source": "ORIGINAL",
        "price_min": stats[6],
        "price_max": stats[7],

        "return_cancel_source":
            "NO explicit return/cancel",

        "return_cancel_rows": None,

        "purchase_rows": stats[8],

        "product_master":
            "PARTIAL: attributes embedded in event rows",

        "location_master": "NO",
        "customer_master": "NO",

        "large_join_possible":
            "LIMITED: mainly event-table aggregation; "
            "category/brand embedded",

        "date_partition_possible":
            "YES: event_time",

        "status": "OK",
    })

except Exception as e:
    row["status"] = "ERROR"
    row["error"] = str(e)

row["scan_seconds"] = round(
    time.perf_counter() - start,
    2
)

results.append(row)
save()

print(
    f"완료: {row['scan_seconds']}초 "
    f"[{row['status']}]"
)


# ============================================================
# FINISH
# ============================================================

save()

print("\n" + "=" * 72)
print("최종 3개 데이터셋 오디션 완료")
print(f"결과 파일: {OUT.name}")
print("=" * 72)

for row in results:
    print(
        f"{row['dataset']:12} "
        f"| rows={row['fact_rows']} "
        f"| size={row['fact_size_gb']} GB "
        f"| status={row['status']}"
    )