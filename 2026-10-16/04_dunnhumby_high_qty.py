from pathlib import Path
import csv
import duckdb

BASE = Path.cwd()
OUT = BASE / "audit_dunnhumby_high_qty.csv"

tx = (
    BASE / "01_dunnhumby/transaction_data.csv"
).resolve().as_posix()

product = (
    BASE / "01_dunnhumby/product.csv"
).resolve().as_posix()

con = duckdb.connect()
con.execute("PRAGMA threads=4")

sql = f"""
WITH transactions AS (
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
),

high_products AS (
    SELECT DISTINCT PRODUCT_ID
    FROM transactions
    WHERE QUANTITY >= 100
)

SELECT
    t.PRODUCT_ID,

    p.DEPARTMENT,
    p.BRAND,
    p.COMMODITY_DESC,
    p.SUB_COMMODITY_DESC,
    p.CURR_SIZE_OF_PRODUCT,

    COUNT(*) AS total_transaction_rows,

    COUNT(*) FILTER (
        WHERE t.QUANTITY >= 100
    ) AS high_quantity_rows,

    MIN(t.QUANTITY) AS min_quantity,
    MAX(t.QUANTITY) AS max_quantity,

    ROUND(
        AVG(t.QUANTITY),
        2
    ) AS avg_quantity,

    quantile_cont(
        t.QUANTITY,
        0.5
    ) AS median_quantity,

    MIN(t.SALES_VALUE) FILTER (
        WHERE t.QUANTITY >= 100
    ) AS high_qty_min_sales_value,

    MAX(t.SALES_VALUE) FILTER (
        WHERE t.QUANTITY >= 100
    ) AS high_qty_max_sales_value,

    COUNT(DISTINCT t.STORE_ID)
        AS store_count,

    COUNT(DISTINCT t.BASKET_ID)
        AS basket_count

FROM transactions t

JOIN high_products h
    ON t.PRODUCT_ID = h.PRODUCT_ID

LEFT JOIN products p
    ON t.PRODUCT_ID = p.PRODUCT_ID

GROUP BY
    t.PRODUCT_ID,
    p.DEPARTMENT,
    p.BRAND,
    p.COMMODITY_DESC,
    p.SUB_COMMODITY_DESC,
    p.CURR_SIZE_OF_PRODUCT

ORDER BY
    max_quantity DESC
"""

cur = con.execute(sql)

columns = [d[0] for d in cur.description]
rows = cur.fetchall()

with open(
    OUT,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

print("=" * 70)
print("Dunnhumby 고수량 상품 검사 완료")
print(f"고수량 상품 수: {len(rows):,}")
print(f"결과 파일: {OUT.name}")
print("=" * 70)

print("\n카테고리 확인용:")
for row in rows:
    print(
        f"{row[0]} | "
        f"MAX={row[8]} | "
        f"{row[1]} | "
        f"{row[3]} | "
        f"{row[4]} | "
        f"{row[5]}"
    )