"""shop.db 새로 만들기 (샘플 주문 포함)

실행: python tools/make_shop_db.py
- 기존 shop.db 는 shop.db.bak 으로 옮겨 둡니다.
- 어제까지 70일치 주문을 만들어 넣습니다. (같은 날 실행하면 같은 데이터)
"""
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "shop.db"
DAYS = 70

MENUS = [
    # id, 이름, 이모지, R가격, L가격, 소개, 딱지, 인기 가중치, L 선택 확률
    (1, "페퍼로니", "🍕", 18900, 24900, "짭짤한 페퍼로니를 빈틈없이", "1등 메뉴", 28, 0.55),
    (2, "불고기", "🥩", 21900, 27900, "달콤 짭짤한 한국식 불고기", "", 17, 0.60),
    (3, "고구마", "🍠", 20900, 26900, "고구마 무스와 콘의 조합", "", 16, 0.55),
    (4, "포테이토", "🥔", 20900, 26900, "웨지 감자와 베이컨", "", 15, 0.55),
    (5, "마르게리타", "🌿", 17900, 22900, "토마토, 모차렐라, 바질. 기본에 충실", "", 14, 0.40),
    (6, "하와이안", "🍍", 19900, 25900, "파인애플은 피자에 올려도 되는가", "논쟁 메뉴", 4, 0.12),
]
CRUSTS = {"기본": 0, "치즈크러스트": 3000, "고구마무스": 2000}
HOURS = {11: 3, 12: 9, 13: 6, 14: 2, 15: 2, 16: 3, 17: 7, 18: 12, 19: 14, 20: 9, 21: 5, 22: 3}
PER_DAY = {0: 19, 1: 18, 2: 20, 3: 21, 4: 30, 5: 34, 6: 26}   # 월~일


def pick(weights):
    return random.choices(list(weights), weights=list(weights.values()))[0]


def main():
    random.seed(date.today().isoformat())
    if DB_PATH.exists():
        DB_PATH.replace(DB_PATH.with_suffix(".db.bak"))

    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE menus (
            id          INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL,
            emoji       TEXT    NOT NULL,
            price_r     INTEGER NOT NULL,
            price_l     INTEGER NOT NULL,
            description TEXT    NOT NULL DEFAULT '',
            tag         TEXT    NOT NULL DEFAULT ''
        );
        CREATE TABLE orders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ordered_at TEXT    NOT NULL,              -- 'YYYY-MM-DD HH:MM:SS'
            menu_id    INTEGER NOT NULL REFERENCES menus(id),
            size       TEXT    NOT NULL CHECK (size IN ('R', 'L')),
            crust      TEXT    NOT NULL,
            qty        INTEGER NOT NULL CHECK (qty BETWEEN 1 AND 10),
            amount     INTEGER NOT NULL,
            channel    TEXT    NOT NULL CHECK (channel IN ('배달', '포장', '매장'))
        );
        CREATE INDEX idx_orders_time ON orders(ordered_at);
    """)
    conn.executemany("INSERT INTO menus VALUES (?, ?, ?, ?, ?, ?, ?)", [m[:7] for m in MENUS])

    menu_w = {m: m[7] for m in MENUS}
    rows = []
    first = date.today() - timedelta(days=DAYS)
    for d in range(DAYS):
        day = first + timedelta(days=d)
        count = PER_DAY[day.weekday()] + random.randint(-4, 4)
        for _ in range(count):
            m = pick(menu_w)
            hour = pick(HOURS)
            at = datetime(day.year, day.month, day.day, hour, random.randint(0, 59), random.randint(0, 59))
            size = "L" if random.random() < m[8] else "R"
            crust = pick({"기본": 50, "치즈크러스트": 45 if size == "L" else 25, "고구마무스": 15})
            qty = pick({1: 75, 2: 20, 3: 5})
            channel = pick({"배달": 60, "포장": 25, "매장": 15} if hour >= 16 else {"배달": 40, "포장": 25, "매장": 35})
            amount = ((m[4] if size == "L" else m[3]) + CRUSTS[crust]) * qty
            rows.append((at.strftime("%Y-%m-%d %H:%M:%S"), m[0], size, crust, qty, amount, channel))
    rows.sort()
    conn.executemany(
        "INSERT INTO orders (ordered_at, menu_id, size, crust, qty, amount, channel) VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ {DB_PATH.name} 생성: 메뉴 {len(MENUS)}개, 주문 {len(rows)}건 ({first} ~ {first + timedelta(days=DAYS - 1)})")


if __name__ == "__main__":
    main()
