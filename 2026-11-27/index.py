"""Inventory Lab: read-only inventory API for AWS Lambda / HTTP API v2."""
import json
import os
import time
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

CA_FILE = os.path.join(os.path.dirname(__file__), "rds-ca.pem")

WAREHOUSE_SUMMARY_SQL = """
SELECT w.warehouse_id, w.name AS warehouse_name,
       COUNT(*) AS product_count,
       SUM(i.quantity_on_hand) AS total_quantity
FROM inventory AS i
JOIN warehouses AS w ON w.warehouse_id = i.warehouse_id
GROUP BY w.warehouse_id, w.name
ORDER BY w.warehouse_id
"""

PRODUCT_SQL = """
SELECT i.product_id, p.sku, p.name AS product_name,
       i.warehouse_id, w.name AS warehouse_name, i.quantity_on_hand
FROM inventory AS i
JOIN products AS p ON p.product_id = i.product_id
JOIN warehouses AS w ON w.warehouse_id = i.warehouse_id
WHERE i.product_id = %s
ORDER BY i.warehouse_id
"""


def response(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False, default=str),
    }


def log_event(name: str, request_id: str, **fields: Any) -> None:
    print(json.dumps({"event": name, "request_id": request_id, **fields}))


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_id = context.aws_request_id
    start = time.perf_counter()
    params = event.get("queryStringParameters") or {}
    product_id = None
    if "product_id" in params:
        try:
            product_id = int(params["product_id"])
            if not 1 <= product_id <= 2**63 - 1:
                raise ValueError
        except (TypeError, ValueError):
            return response(400, {"error": "product_id must be a positive integer"})

    connection_start = time.perf_counter()
    try:
        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            port=3306,
            charset="utf8mb4",
            connect_timeout=3,
            read_timeout=5,
            write_timeout=5,
            ssl_ca=CA_FILE,
            ssl_verify_cert=True,
            ssl_verify_identity=True,
            autocommit=True,
            cursorclass=DictCursor,
        )
    except pymysql.MySQLError as exc:
        log_event("DB_CONNECTION_ERROR", request_id,
                  error_type=type(exc).__name__,
                  error_code=exc.args[0] if exc.args else None,
                  elapsed_ms=elapsed_ms(connection_start))
        return response(503, {"error": "Database unavailable", "request_id": request_id})

    connect_ms = elapsed_ms(connection_start)
    query_start = time.perf_counter()
    try:
        with connection.cursor() as cursor:
            if product_id is None:
                cursor.execute(WAREHOUSE_SUMMARY_SQL)
            else:
                cursor.execute(PRODUCT_SQL, (product_id,))
            rows = cursor.fetchall()
        query_ms = elapsed_ms(query_start)
        # MySQL SUM(BIGINT) returns Decimal. Quantities are integer counts.
        for row in rows:
            if "total_quantity" in row:
                row["total_quantity"] = int(row["total_quantity"])
        log_event("REQUEST_OK", request_id, rows=len(rows),
                  connect_ms=connect_ms, query_ms=query_ms,
                  elapsed_ms=elapsed_ms(start))
        return response(200, {"count": len(rows), "data": rows, "request_id": request_id})
    except pymysql.MySQLError as exc:
        log_event("DB_QUERY_ERROR", request_id,
                  error_type=type(exc).__name__,
                  error_code=exc.args[0] if exc.args else None)
        return response(500, {"error": "Database query failed", "request_id": request_id})
    finally:
        connection.close()
