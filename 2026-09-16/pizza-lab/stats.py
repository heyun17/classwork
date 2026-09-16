"""대시보드용 집계 (5장)

원본 주문을 그대로 쓰지 않고, SQL 로 '합계 · 개수 · 순위'를 만들어
화면과 AI 가 쓰기 좋은 작은 딕셔너리로 돌려줍니다.
"""
from datetime import date, timedelta

from db import get_conn


def one_value(sql, params=()):
    """결과가 한 칸뿐인 SQL 실행"""
    conn = get_conn()
    value = conn.execute(sql, params).fetchone()[0]
    conn.close()
    return value


def latest_day():
    """DB의 마지막 주문 날짜 = 대시보드 기준일"""
    value = one_value("SELECT MAX(date(ordered_at)) FROM orders")
    return date.fromisoformat(value) if value else date.today()


def first_day():
    """DB의 첫 주문 날짜"""
    value = one_value("SELECT MIN(date(ordered_at)) FROM orders")
    return date.fromisoformat(value) if value else date.today()


# 모든 집계에 붙는 기간 조건
IN_PERIOD = "date(o.ordered_at) BETWEEN ? AND ?"

SQL_TOTAL = f"""
    SELECT COALESCE(SUM(amount), 0), COUNT(*), COALESCE(SUM(qty), 0)
    FROM orders o WHERE {IN_PERIOD}"""

SQL_SALES = f"""
    SELECT COALESCE(SUM(amount), 0)
    FROM orders o WHERE {IN_PERIOD}"""

SQL_DAILY = f"""
    SELECT date(o.ordered_at) AS day, SUM(amount) AS sales, COUNT(*) AS orders
    FROM orders o WHERE {IN_PERIOD}
    GROUP BY day ORDER BY day"""

SQL_BY_MENU = f"""
    SELECT m.name, m.emoji, SUM(o.qty) AS qty, SUM(o.amount) AS sales,
           SUM(CASE WHEN o.size = 'L' THEN o.qty ELSE 0 END) AS l_qty
    FROM orders o JOIN menus m ON m.id = o.menu_id
    WHERE {IN_PERIOD}
    GROUP BY m.id ORDER BY qty DESC"""

SQL_BY_HOUR = f"""
    SELECT CAST(strftime('%H', o.ordered_at) AS INTEGER) AS hour,
           COUNT(*) AS orders
    FROM orders o WHERE {IN_PERIOD}
    GROUP BY hour ORDER BY hour"""

SQL_BY_CHANNEL = f"""
    SELECT channel AS name, COUNT(*) AS n
    FROM orders o WHERE {IN_PERIOD}
    GROUP BY channel ORDER BY n DESC"""

SQL_BY_CRUST = f"""
    SELECT crust AS name, SUM(qty) AS n
    FROM orders o WHERE {IN_PERIOD}
    GROUP BY crust ORDER BY n DESC"""


def with_pct(rows):
    """[{name, n}] 에 비율(pct)을 붙이기"""
    total = sum(r["n"] for r in rows) or 1      # 0으로 나누기 방지
    result = []
    for r in rows:
        pct = round(r["n"] * 100 / total)
        result.append({"name": r["name"], "n": r["n"], "pct": pct})
    return result


def summary(days=7):
    # ── 기간 정하기: 기준일부터 거꾸로 days 일
    end = latest_day()
    start = end - timedelta(days=days - 1)
    prev_start = start - timedelta(days=days)
    prev_end = start - timedelta(days=1)
    period = (start.isoformat(), end.isoformat())

    # ── SQL 실행
    conn = get_conn()
    sales, orders, pizzas = conn.execute(SQL_TOTAL, period).fetchone()
    prev_sales = conn.execute(
        SQL_SALES, (prev_start.isoformat(), prev_end.isoformat())).fetchone()[0]
    daily = conn.execute(SQL_DAILY, period).fetchall()
    by_menu = conn.execute(SQL_BY_MENU, period).fetchall()
    by_hour = conn.execute(SQL_BY_HOUR, period).fetchall()
    by_channel = conn.execute(SQL_BY_CHANNEL, period).fetchall()
    by_crust = conn.execute(SQL_BY_CRUST, period).fetchall()
    conn.close()

    # ── 직전 기간 대비: 직전 기간 데이터가 온전히 있을 때만
    change = None
    if prev_sales and prev_start >= first_day():
        change = round((sales - prev_sales) * 100 / prev_sales)

    return {
        "days": days,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "sales": sales,
        "orders": orders,
        "pizzas": pizzas,
        "avg": round(sales / orders) if orders else 0,
        "change": change,
        "daily": [dict(r) for r in daily],
        "by_menu": [dict(r) for r in by_menu],
        "by_hour": [dict(r) for r in by_hour],
        "by_channel": with_pct(by_channel),
        "by_crust": with_pct(by_crust),
    }


def to_text(s):
    """AI에게 보낼 요약문. 원본 주문 대신 이 몇 줄만 보냅니다."""
    lines = [
        f"기간: {s['start']} ~ {s['end']} ({s['days']}일)",
        f"매출: {s['sales']:,}원 / 주문 {s['orders']}건 / {s['pizzas']}판"
        f" / 주문당 평균 {s['avg']:,}원",
    ]
    if s["change"] is not None:
        lines.append(f"직전 같은 기간 대비 매출: {s['change']:+d}%")

    menus = [f"{m['name']} {m['qty']}판(L {m['l_qty']}) {m['sales']:,}원"
             for m in s["by_menu"]]
    lines.append("메뉴별(판 수, 그중 L 사이즈, 매출): " + ", ".join(menus))

    if s["by_hour"]:
        top3 = sorted(s["by_hour"], key=lambda h: h["orders"], reverse=True)[:3]
        hours = [f"{h['hour']}시 {h['orders']}건" for h in top3]
        lines.append("주문 많은 시간대: " + ", ".join(hours))

    channels = [f"{c['name']} {c['pct']}%" for c in s["by_channel"]]
    crusts = [f"{c['name']} {c['pct']}%" for c in s["by_crust"]]
    lines.append("채널: " + ", ".join(channels))
    lines.append("엣지: " + ", ".join(crusts))
    return "\n".join(lines)
