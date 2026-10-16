from pathlib import Path
import csv
import json
import time
import duckdb

BASE = Path.cwd()
OUT = BASE / "audit_top3_patterns.csv"

con = duckdb.connect()
con.execute("PRAGMA threads=4")

FIELDS = [
    "dataset",
    "section",
    "metric",
    "value",
    "detail",
]

results = []


def p(relative_path):
    return (
        (BASE / relative_path)
        .resolve()
        .as_posix()
        .replace("'", "''")
    )


def add(dataset, section, metric, value, detail=""):
    results.append({
        "dataset": dataset,
        "section": section,
        "metric": metric,
        "value": value,
        "detail": detail,
    })


def save():
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)


# ============================================================
# 1. Dunnhumby
# ============================================================

print("\n" + "=" * 70)
print("검사 중: Dunnhumby - 수량 분포 / 극단값")

started = time.perf_counter()

tx = p("01_dunnhumby/transaction_data.csv")
product = p("01_dunnhumby/product.csv")

stats = con.execute(
    f"""
    SELECT
        COUNT(*) AS total_rows,
        MIN(QUANTITY) AS min_qty,
        MAX(QUANTITY) AS max_qty,
        AVG(QUANTITY) AS avg_qty,

        quantile_cont(QUANTITY, 0.50) AS p50,
        quantile_cont(QUANTITY, 0.90) AS p90,
        quantile_cont(QUANTITY, 0.95) AS p95,
        quantile_cont(QUANTITY, 0.99) AS p99,
        quantile_cont(QUANTITY, 0.999) AS p999,

        COUNT(*) FILTER (
            WHERE QUANTITY = 0
        ) AS qty_0,

        COUNT(*) FILTER (
            WHERE QUANTITY = 1
        ) AS qty_1,

        COUNT(*) FILTER (
            WHERE QUANTITY = 2
        ) AS qty_2,

        COUNT(*) FILTER (
            WHERE QUANTITY = 3
        ) AS qty_3,

        COUNT(*) FILTER (
            WHERE QUANTITY >= 10
        ) AS qty_ge_10,

        COUNT(*) FILTER (
            WHERE QUANTITY >= 100
        ) AS qty_ge_100,

        COUNT(*) FILTER (
            WHERE QUANTITY >= 1000
        ) AS qty_ge_1000,

        COUNT(DISTINCT PRODUCT_ID) FILTER (
            WHERE QUANTITY >= 100
        ) AS products_ge_100,

        COUNT(*) FILTER (
            WHERE QUANTITY = 0
            AND SALES_VALUE = 0
        ) AS qty0_value0,

        COUNT(*) FILTER (
            WHERE QUANTITY = 0
            AND SALES_VALUE <> 0
        ) AS qty0_value_nonzero

    FROM read_csv_auto(
        '{tx}',
        header=true
    )
    """
).fetchone()

names = [
    "total_rows",
    "quantity_min",
    "quantity_max",
    "quantity_avg",
    "quantity_p50",
    "quantity_p90",
    "quantity_p95",
    "quantity_p99",
    "quantity_p99_9",
    "quantity_eq_0",
    "quantity_eq_1",
    "quantity_eq_2",
    "quantity_eq_3",
    "quantity_ge_10",
    "quantity_ge_100",
    "quantity_ge_1000",
    "products_with_qty_ge_100",
    "qty0_and_sales_value0",
    "qty0_and_sales_value_nonzero",
]

for name, value in zip(names, stats):
    add(
        "Dunnhumby",
        "quantity_summary",
        name,
        value
    )


top_qty = con.execute(
    f"""
    WITH tx AS (
        SELECT *
        FROM read_csv_auto(
            '{tx}',
            header=true
        )
    ),
    products AS (
        SELECT *
        FROM read_csv_auto(
            '{product}',
            header=true
        )
    )
    SELECT
        t.BASKET_ID,
        t.PRODUCT_ID,
        t.QUANTITY,
        t.SALES_VALUE,
        t.STORE_ID,
        t.household_key,
        t.DAY,
        t.TRANS_TIME,
        p.DEPARTMENT,
        p.COMMODITY_DESC,
        p.SUB_COMMODITY_DESC,
        p.CURR_SIZE_OF_PRODUCT
    FROM tx t
    LEFT JOIN products p
        ON t.PRODUCT_ID = p.PRODUCT_ID
    ORDER BY t.QUANTITY DESC
    LIMIT 20
    """
).fetchall()

top_cols = [
    "basket_id",
    "product_id",
    "quantity",
    "sales_value",
    "store_id",
    "household_key",
    "day",
    "trans_time",
    "department",
    "commodity",
    "sub_commodity",
    "size",
]

for i, row in enumerate(top_qty, start=1):
    data = dict(zip(top_cols, row))

    add(
        "Dunnhumby",
        "top_quantity_rows",
        f"rank_{i}",
        data["quantity"],
        json.dumps(
            data,
            ensure_ascii=False,
            default=str
        )
    )

print(
    f"완료: {time.perf_counter() - started:.2f}초"
)


# ============================================================
# 2. Pakistan E-Commerce
# ============================================================

print("\n" + "=" * 70)
print("검사 중: Pakistan - 주문 상태 분포")

started = time.perf_counter()

pakistan = p(
    "02_pakistan/Pakistan Largest Ecommerce Dataset.csv"
)

status_rows = con.execute(
    f"""
    WITH src AS (
        SELECT
            NULLIF(
                TRIM(item_id),
                ''
            ) AS item_id,

            COALESCE(
                NULLIF(TRIM(status), ''),
                '[NULL/BLANK]'
            ) AS status_clean,

            NULLIF(
                TRIM(increment_id),
                ''
            ) AS order_id,

            TRY_CAST(
                qty_ordered AS BIGINT
            ) AS qty,

            TRY_CAST(
                price AS DOUBLE
            ) AS price

        FROM read_csv_auto(
            '{pakistan}',
            header=true,
            all_varchar=true
        )
    )
    SELECT
        status_clean,
        COUNT(*) AS row_count,
        COUNT(DISTINCT order_id)
            AS order_count,
        MIN(qty) AS min_qty,
        MAX(qty) AS max_qty,
        AVG(price) AS avg_price
    FROM src
    WHERE item_id IS NOT NULL
    GROUP BY status_clean
    ORDER BY row_count DESC
    """
).fetchall()

total_status_rows = sum(row[1] for row in status_rows)

for row in status_rows:
    (
        status_name,
        row_count,
        order_count,
        min_qty,
        max_qty,
        avg_price,
    ) = row

    pct = (
        row_count / total_status_rows * 100
        if total_status_rows
        else 0
    )

    detail = {
        "row_count": row_count,
        "row_percent": round(pct, 2),
        "distinct_orders": order_count,
        "quantity_min": min_qty,
        "quantity_max": max_qty,
        "average_price": (
            round(avg_price, 2)
            if avg_price is not None
            else None
        ),
    }

    add(
        "Pakistan E-Commerce",
        "status_distribution",
        status_name,
        row_count,
        json.dumps(
            detail,
            ensure_ascii=False,
            default=str
        )
    )

print(
    f"완료: {time.perf_counter() - started:.2f}초"
)


# ============================================================
# 3. Online Retail II
# ============================================================

print("\n" + "=" * 70)
print(
    "검사 중: Online Retail II - "
    "음수 수량 / 취소 Invoice 관계"
)

started = time.perf_counter()

online = p(
    "03_online_retail/online_retail_II.csv"
)

summary = con.execute(
    f"""
    SELECT
        COUNT(*) AS total_rows,

        COUNT(*) FILTER (
            WHERE Quantity < 0
        ) AS negative_qty_rows,

        COUNT(*) FILTER (
            WHERE Invoice LIKE 'C%'
        ) AS c_invoice_rows,

        COUNT(*) FILTER (
            WHERE Quantity < 0
            AND Invoice LIKE 'C%'
        ) AS negative_and_c,

        COUNT(*) FILTER (
            WHERE Quantity < 0
            AND (
                Invoice NOT LIKE 'C%'
                OR Invoice IS NULL
            )
        ) AS negative_not_c,

        COUNT(*) FILTER (
            WHERE Quantity >= 0
            AND Invoice LIKE 'C%'
        ) AS nonnegative_and_c,

        COUNT(DISTINCT Invoice) FILTER (
            WHERE Quantity < 0
        ) AS negative_qty_invoices,

        COUNT(DISTINCT Invoice) FILTER (
            WHERE Invoice LIKE 'C%'
        ) AS c_invoices,

        COUNT(*) FILTER (
            WHERE Price < 0
        ) AS negative_price_rows,

        COUNT(*) FILTER (
            WHERE "Customer ID" IS NULL
        ) AS null_customer_rows

    FROM read_csv_auto(
        '{online}',
        header=true
    )
    """
).fetchone()

summary_names = [
    "total_rows",
    "negative_quantity_rows",
    "c_invoice_rows",
    "negative_and_c_rows",
    "negative_not_c_rows",
    "nonnegative_and_c_rows",
    "negative_quantity_invoice_count",
    "c_invoice_count",
    "negative_price_rows",
    "null_customer_rows",
]

for name, value in zip(summary_names, summary):
    add(
        "Online Retail II",
        "cancel_relationship",
        name,
        value
    )


negative_samples = con.execute(
    f"""
    SELECT
        Invoice,
        StockCode,
        Description,
        Quantity,
        InvoiceDate,
        Price,
        "Customer ID",
        Country
    FROM read_csv_auto(
        '{online}',
        header=true
    )
    WHERE Quantity < 0
    ORDER BY Quantity ASC
    LIMIT 20
    """
).fetchall()

neg_cols = [
    "invoice",
    "stock_code",
    "description",
    "quantity",
    "invoice_date",
    "price",
    "customer_id",
    "country",
]

for i, row in enumerate(
    negative_samples,
    start=1
):
    data = dict(zip(neg_cols, row))

    add(
        "Online Retail II",
        "largest_negative_quantity_rows",
        f"rank_{i}",
        data["quantity"],
        json.dumps(
            data,
            ensure_ascii=False,
            default=str
        )
    )

print(
    f"완료: {time.perf_counter() - started:.2f}초"
)


# ============================================================
# 저장
# ============================================================

save()

print("\n" + "=" * 70)
print("전체 완료")
print(f"결과 파일: {OUT.name}")