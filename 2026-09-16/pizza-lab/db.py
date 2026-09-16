"""shop.db 읽기·쓰기 (3장)

SQLite 는 파일 하나짜리 데이터베이스입니다.
함수마다 '연결 → SQL 실행 → (저장) → 닫기' 순서를 지킵니다.
"""
import sqlite3
from pathlib import Path

# app.py 와 같은 폴더의 shop.db (어디서 실행해도 같은 파일)
DB_PATH = Path(__file__).parent / "shop.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # 결과를 row["name"] 처럼 이름으로 꺼내기
    return conn


# ── 메뉴 ─────────────────────────────────────
def get_menus():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM menus ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]      # Row → 딕셔너리 (템플릿·JSON에서 쓰기 쉽게)


def get_menu(menu_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM menus WHERE id = ?", (menu_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── 주문 ─────────────────────────────────────
def add_order(menu_id, size, crust, qty, channel, amount):
    """주문 한 건 저장하고 새 주문 번호를 돌려준다"""
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO orders (ordered_at, menu_id, size, crust, qty, amount, channel)
           VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?)""",
        (menu_id, size, crust, qty, amount, channel),
    )
    conn.commit()                       # 저장 확정 (빠뜨리면 기록되지 않음)
    new_id = cur.lastrowid
    conn.close()
    return new_id


ORDER_SELECT = """
    SELECT o.id, o.ordered_at, o.size, o.crust, o.qty, o.amount, o.channel,
           o.menu_id, m.name AS menu_name, m.emoji
    FROM orders AS o
    JOIN menus  AS m ON m.id = o.menu_id
"""


def get_order(order_id):
    conn = get_conn()
    row = conn.execute(ORDER_SELECT + " WHERE o.id = ?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_orders(channel=None, limit=50):
    """최근 주문 목록. channel 을 주면 그 채널만."""
    sql = ORDER_SELECT
    params = []
    if channel:
        sql += " WHERE o.channel = ?"
        params.append(channel)
    sql += " ORDER BY o.id DESC LIMIT ?"
    params.append(limit)

    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_orders(channel=None):
    conn = get_conn()
    if channel:
        n = conn.execute("SELECT COUNT(*) FROM orders WHERE channel = ?", (channel,)).fetchone()[0]
    else:
        n = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    return n
