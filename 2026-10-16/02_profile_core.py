from pathlib import Path
import csv
import time
import duckdb

BASE = Path.cwd()
OUT = BASE / "audit_core_profile.csv"

con = duckdb.connect()
con.execute("PRAGMA threads=4")

FIELDS = [
    "dataset",
    "source",
    "raw_rows",
    "valid_rows",
    "order_count",
    "product_count",
    "customer_count",
    "location_count",
    "channel_count",
    "period_type",
    "period_min",
    "period_max",
    "quantity_available",
    "quantity_min",
    "quantity_max",
    "quantity_zero_rows",
    "quantity_negative_rows",
    "value_field",
    "value_min",
    "value_max",
    "value_zero_rows",
    "value_negative_rows",
    "status_distinct_count",
    "cancel_return_rows",
    "null_order_id",
    "null_product_id",
    "null_customer_id",
    "null_location",
    "null_period",
    "null_quantity",
    "null_value",
    "scan_seconds",
    "status",
    "notes",
    "error",
]

results = []


def p(relative_path):
    """DuckDB SQL에서 사용할 안전한 절대경로"""
    return (
        (BASE / relative_path)
        .resolve()
        .as_posix()
        .replace("'", "''")
    )


def save_results():
    """중간 실패가 발생해도 완료된 결과까지 저장"""
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)


def run_profile(dataset, source, sql, notes):
    print("\n" + "=" * 70)
    print(f"검사 중: {dataset}")
    print(f"원본: {source}")

    started = time.perf_counter()

    row = {field: None for field in FIELDS}
    row["dataset"] = dataset
    row["source"] = source
    row["notes"] = notes

    try:
        cur = con.execute(sql)
        values = cur.fetchone()
        columns = [d[0] for d in cur.description]

        row.update(dict(zip(columns, values)))
        row["status"] = "OK"

    except Exception as e:
        row["status"] = "ERROR"
        row["error"] = str(e)
        print(f"ERROR: {e}")

    row["scan_seconds"] = round(
        time.perf_counter() - started,
        2
    )

    results.append(row)
    save_results()

    print(f"완료: {row['scan_seconds']}초")


# ============================================================
# 1. Dunnhumby
# ============================================================

dunnhumby = p(
    "01_dunnhumby/transaction_data.csv"
)

run_profile(
    dataset="Dunnhumby",
    source="transaction_data.csv",
    notes=(
        "BASKET_ID=주문/장바구니, PRODUCT_ID=상품, "
        "STORE_ID=매장. DAY는 실제 날짜가 아닌 익명화된 일차. "
        "SALES_VALUE는 거래행 판매금액."
    ),
    sql=f"""
        SELECT
            COUNT(*) AS raw_rows,
            COUNT(*) AS valid_rows,

            COUNT(DISTINCT BASKET_ID)
                AS order_count,

            COUNT(DISTINCT PRODUCT_ID)
                AS product_count,

            COUNT(DISTINCT household_key)
                AS customer_count,

            COUNT(DISTINCT STORE_ID)
                AS location_count,

            NULL::BIGINT AS channel_count,

            'DAY number' AS period_type,

            CAST(MIN(DAY) AS VARCHAR)
                AS period_min,

            CAST(MAX(DAY) AS VARCHAR)
                AS period_max,

            'YES' AS quantity_available,

            MIN(QUANTITY)
                AS quantity_min,

            MAX(QUANTITY)
                AS quantity_max,

            COUNT(*) FILTER (
                WHERE QUANTITY = 0
            ) AS quantity_zero_rows,

            COUNT(*) FILTER (
                WHERE QUANTITY < 0
            ) AS quantity_negative_rows,

            'SALES_VALUE' AS value_field,

            MIN(SALES_VALUE)
                AS value_min,

            MAX(SALES_VALUE)
                AS value_max,

            COUNT(*) FILTER (
                WHERE SALES_VALUE = 0
            ) AS value_zero_rows,

            COUNT(*) FILTER (
                WHERE SALES_VALUE < 0
            ) AS value_negative_rows,

            NULL::BIGINT
                AS status_distinct_count,

            NULL::BIGINT
                AS cancel_return_rows,

            COUNT(*) FILTER (
                WHERE BASKET_ID IS NULL
            ) AS null_order_id,

            COUNT(*) FILTER (
                WHERE PRODUCT_ID IS NULL
            ) AS null_product_id,

            COUNT(*) FILTER (
                WHERE household_key IS NULL
            ) AS null_customer_id,

            COUNT(*) FILTER (
                WHERE STORE_ID IS NULL
            ) AS null_location,

            COUNT(*) FILTER (
                WHERE DAY IS NULL
            ) AS null_period,

            COUNT(*) FILTER (
                WHERE QUANTITY IS NULL
            ) AS null_quantity,

            COUNT(*) FILTER (
                WHERE SALES_VALUE IS NULL
            ) AS null_value

        FROM read_csv_auto(
            '{dunnhumby}',
            header=true
        )
    """,
)


# ============================================================
# 2. Pakistan E-Commerce
# ============================================================

pakistan = p(
    "02_pakistan/Pakistan Largest Ecommerce Dataset.csv"
)

run_profile(
    dataset="Pakistan E-Commerce",
    source="Pakistan Largest Ecommerce Dataset.csv",
    notes=(
        "CSV 전체를 VARCHAR로 읽은 뒤 필요한 숫자만 TRY_CAST. "
        "increment_id와 Customer ID는 계산용 숫자가 아닌 식별자로 처리. "
        "빈 행 및 #N/A 등 데이터 품질 문제도 확인."
    ),
    sql=f"""
        WITH src AS (
            SELECT
                *,

                TRY_CAST(
                    price AS DOUBLE
                ) AS price_num,

                TRY_CAST(
                    qty_ordered AS BIGINT
                ) AS qty_ordered_num,

                COALESCE(
                    CAST(
                        TRY_STRPTIME(
                            created_at,
                            '%m/%d/%Y'
                        ) AS DATE
                    ),
                    TRY_CAST(
                        created_at AS DATE
                    )
                ) AS parsed_date

            FROM read_csv_auto(
                '{pakistan}',
                header=true,
                all_varchar=true
            )
        ),

        cleaned AS (
            SELECT
                *,

                NULLIF(
                    TRIM(item_id),
                    ''
                ) AS item_id_clean,

                NULLIF(
                    TRIM(increment_id),
                    ''
                ) AS order_id_clean,

                NULLIF(
                    TRIM(sku),
                    ''
                ) AS sku_clean,

                CASE
                    WHEN "Customer ID" IS NULL
                        THEN NULL
                    WHEN TRIM("Customer ID") = ''
                        THEN NULL
                    WHEN UPPER(TRIM("Customer ID"))
                        IN (
                            '#N/A',
                            'N/A',
                            'NULL',
                            '\\N'
                        )
                        THEN NULL
                    ELSE TRIM("Customer ID")
                END AS customer_id_clean

            FROM src
        )

        SELECT
            COUNT(*) AS raw_rows,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
            ) AS valid_rows,

            COUNT(DISTINCT order_id_clean)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS order_count,

            COUNT(DISTINCT sku_clean)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS product_count,

            COUNT(DISTINCT customer_id_clean)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS customer_count,

            NULL::BIGINT
                AS location_count,

            NULL::BIGINT
                AS channel_count,

            'calendar date'
                AS period_type,

            CAST(
                MIN(parsed_date)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS VARCHAR
            ) AS period_min,

            CAST(
                MAX(parsed_date)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS VARCHAR
            ) AS period_max,

            'YES'
                AS quantity_available,

            MIN(qty_ordered_num)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS quantity_min,

            MAX(qty_ordered_num)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS quantity_max,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND qty_ordered_num = 0
            ) AS quantity_zero_rows,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND qty_ordered_num < 0
            ) AS quantity_negative_rows,

            'price'
                AS value_field,

            MIN(price_num)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS value_min,

            MAX(price_num)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS value_max,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND price_num = 0
            ) AS value_zero_rows,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND price_num < 0
            ) AS value_negative_rows,

            COUNT(DISTINCT status)
                FILTER (
                    WHERE item_id_clean IS NOT NULL
                )
                AS status_distinct_count,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND (
                    LOWER(status)
                        LIKE '%cancel%'
                    OR
                    LOWER(status)
                        LIKE '%refund%'
                )
            ) AS cancel_return_rows,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND order_id_clean IS NULL
            ) AS null_order_id,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND sku_clean IS NULL
            ) AS null_product_id,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND customer_id_clean IS NULL
            ) AS null_customer_id,

            NULL::BIGINT
                AS null_location,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND parsed_date IS NULL
            ) AS null_period,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND qty_ordered_num IS NULL
            ) AS null_quantity,

            COUNT(*) FILTER (
                WHERE item_id_clean IS NOT NULL
                AND price_num IS NULL
            ) AS null_value

        FROM cleaned
    """,
)


# ============================================================
# 3. Online Retail II
# ============================================================

online_retail = p(
    "03_online_retail/online_retail_II.csv"
)

run_profile(
    dataset="Online Retail II",
    source="online_retail_II.csv",
    notes=(
        "Invoice=주문, StockCode=상품. "
        "Invoice가 C로 시작하면 취소 거래 후보. "
        "수량 음수와 고객 ID 결측 여부도 확인."
    ),
    sql=f"""
        SELECT
            COUNT(*) AS raw_rows,
            COUNT(*) AS valid_rows,

            COUNT(DISTINCT Invoice)
                AS order_count,

            COUNT(DISTINCT StockCode)
                AS product_count,

            COUNT(DISTINCT "Customer ID")
                AS customer_count,

            NULL::BIGINT
                AS location_count,

            NULL::BIGINT
                AS channel_count,

            'calendar timestamp'
                AS period_type,

            CAST(
                MIN(InvoiceDate)
                AS VARCHAR
            ) AS period_min,

            CAST(
                MAX(InvoiceDate)
                AS VARCHAR
            ) AS period_max,

            'YES'
                AS quantity_available,

            MIN(Quantity)
                AS quantity_min,

            MAX(Quantity)
                AS quantity_max,

            COUNT(*) FILTER (
                WHERE Quantity = 0
            ) AS quantity_zero_rows,

            COUNT(*) FILTER (
                WHERE Quantity < 0
            ) AS quantity_negative_rows,

            'Price'
                AS value_field,

            MIN(Price)
                AS value_min,

            MAX(Price)
                AS value_max,

            COUNT(*) FILTER (
                WHERE Price = 0
            ) AS value_zero_rows,

            COUNT(*) FILTER (
                WHERE Price < 0
            ) AS value_negative_rows,

            NULL::BIGINT
                AS status_distinct_count,

            COUNT(*) FILTER (
                WHERE Invoice LIKE 'C%'
            ) AS cancel_return_rows,

            COUNT(*) FILTER (
                WHERE Invoice IS NULL
            ) AS null_order_id,

            COUNT(*) FILTER (
                WHERE StockCode IS NULL
            ) AS null_product_id,

            COUNT(*) FILTER (
                WHERE "Customer ID" IS NULL
            ) AS null_customer_id,

            NULL::BIGINT
                AS null_location,

            COUNT(*) FILTER (
                WHERE InvoiceDate IS NULL
            ) AS null_period,

            COUNT(*) FILTER (
                WHERE Quantity IS NULL
            ) AS null_quantity,

            COUNT(*) FILTER (
                WHERE Price IS NULL
            ) AS null_value

        FROM read_csv_auto(
            '{online_retail}',
            header=true
        )
    """,
)


# ============================================================
# 4. Instacart
# ============================================================

insta_prior = p(
    "04_instacart/order_products__prior.csv"
)

insta_train = p(
    "04_instacart/order_products__train.csv"
)

insta_orders = p(
    "04_instacart/orders.csv"
)

run_profile(
    dataset="Instacart",
    source=(
        "order_products__prior.csv + "
        "order_products__train.csv + "
        "orders.csv"
    ),
    notes=(
        "주문/주문상세 구조는 명확하지만 실제 구매수량 컬럼 없음. "
        "add_to_cart_order는 수량이 아니라 장바구니 투입 순서. "
        "가격, 실제 날짜, 매장 정보도 없음."
    ),
    sql=f"""
        WITH items AS (
            SELECT
                order_id,
                product_id
            FROM read_csv_auto(
                '{insta_prior}',
                header=true
            )

            UNION ALL

            SELECT
                order_id,
                product_id
            FROM read_csv_auto(
                '{insta_train}',
                header=true
            )
        ),

        ord AS (
            SELECT
                order_id,
                user_id
            FROM read_csv_auto(
                '{insta_orders}',
                header=true
            )
        )

        SELECT
            COUNT(*) AS raw_rows,
            COUNT(*) AS valid_rows,

            COUNT(DISTINCT i.order_id)
                AS order_count,

            COUNT(DISTINCT i.product_id)
                AS product_count,

            COUNT(DISTINCT o.user_id)
                AS customer_count,

            NULL::BIGINT
                AS location_count,

            NULL::BIGINT
                AS channel_count,

            'NO CALENDAR DATE'
                AS period_type,

            NULL::VARCHAR
                AS period_min,

            NULL::VARCHAR
                AS period_max,

            'NO'
                AS quantity_available,

            NULL::BIGINT
                AS quantity_min,

            NULL::BIGINT
                AS quantity_max,

            NULL::BIGINT
                AS quantity_zero_rows,

            NULL::BIGINT
                AS quantity_negative_rows,

            NULL::VARCHAR
                AS value_field,

            NULL::DOUBLE
                AS value_min,

            NULL::DOUBLE
                AS value_max,

            NULL::BIGINT
                AS value_zero_rows,

            NULL::BIGINT
                AS value_negative_rows,

            NULL::BIGINT
                AS status_distinct_count,

            NULL::BIGINT
                AS cancel_return_rows,

            COUNT(*) FILTER (
                WHERE i.order_id IS NULL
            ) AS null_order_id,

            COUNT(*) FILTER (
                WHERE i.product_id IS NULL
            ) AS null_product_id,

            COUNT(*) FILTER (
                WHERE o.user_id IS NULL
            ) AS null_customer_id,

            NULL::BIGINT
                AS null_location,

            NULL::BIGINT
                AS null_period,

            NULL::BIGINT
                AS null_quantity,

            NULL::BIGINT
                AS null_value

        FROM items i

        LEFT JOIN ord o
            ON i.order_id = o.order_id
    """,
)


# ============================================================
# 5. H&M
# ============================================================

hm = p(
    "05_hm/transactions_train.csv"
)

run_profile(
    dataset="H&M",
    source="transactions_train.csv",
    notes=(
        "대규모 실제 구매이력. "
        "고객/상품/날짜/가격/판매채널은 있으나 "
        "order_id, 구매수량, 실제 매장 ID는 없음."
    ),
    sql=f"""
        SELECT
            COUNT(*) AS raw_rows,
            COUNT(*) AS valid_rows,

            NULL::BIGINT
                AS order_count,

            COUNT(DISTINCT article_id)
                AS product_count,

            COUNT(DISTINCT customer_id)
                AS customer_count,

            NULL::BIGINT
                AS location_count,

            COUNT(DISTINCT sales_channel_id)
                AS channel_count,

            'calendar date'
                AS period_type,

            CAST(
                MIN(t_dat)
                AS VARCHAR
            ) AS period_min,

            CAST(
                MAX(t_dat)
                AS VARCHAR
            ) AS period_max,

            'NO'
                AS quantity_available,

            NULL::BIGINT
                AS quantity_min,

            NULL::BIGINT
                AS quantity_max,

            NULL::BIGINT
                AS quantity_zero_rows,

            NULL::BIGINT
                AS quantity_negative_rows,

            'price'
                AS value_field,

            MIN(price)
                AS value_min,

            MAX(price)
                AS value_max,

            COUNT(*) FILTER (
                WHERE price = 0
            ) AS value_zero_rows,

            COUNT(*) FILTER (
                WHERE price < 0
            ) AS value_negative_rows,

            NULL::BIGINT
                AS status_distinct_count,

            NULL::BIGINT
                AS cancel_return_rows,

            NULL::BIGINT
                AS null_order_id,

            COUNT(*) FILTER (
                WHERE article_id IS NULL
            ) AS null_product_id,

            COUNT(*) FILTER (
                WHERE customer_id IS NULL
            ) AS null_customer_id,

            NULL::BIGINT
                AS null_location,

            COUNT(*) FILTER (
                WHERE t_dat IS NULL
            ) AS null_period,

            NULL::BIGINT
                AS null_quantity,

            COUNT(*) FILTER (
                WHERE price IS NULL
            ) AS null_value

        FROM read_csv_auto(
            '{hm}',
            header=true
        )
    """,
)


# ============================================================
# 저장
# ============================================================

save_results()

print("\n" + "=" * 70)
print("전체 완료")
print(f"결과 파일: {OUT.name}")