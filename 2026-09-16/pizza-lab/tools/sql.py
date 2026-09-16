"""shop.db 에 SQL 을 실행해 표로 보여주기 (3장)

사용법
  python tools/sql.py "SELECT * FROM menus"      한 번 실행
  python tools/sql.py                            여러 번 입력 (빈 줄 Enter 로 종료)

SELECT 가 아닌 문장(INSERT · UPDATE · DELETE)은 실행 후 바로 저장합니다.
"""
import sqlite3
import sys
import unicodedata
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "shop.db"
MAX_ROWS = 30


def width(text):
    """한글·이모지는 두 칸으로 계산"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, w):
    return text + " " * (w - width(text))


def show(cur):
    if cur.description is None:                      # SELECT 가 아닌 경우
        print(f"✅ 완료 · 바뀐 행 {cur.rowcount}개")
        return
    names = [d[0] for d in cur.description]
    rows = cur.fetchmany(MAX_ROWS + 1)
    cells = [[("" if v is None else str(v)) for v in r] for r in rows[:MAX_ROWS]]
    widths = [max([width(n)] + [width(r[i]) for r in cells]) for i, n in enumerate(names)]
    print(" | ".join(pad(n, w) for n, w in zip(names, widths)))
    print("-+-".join("-" * w for w in widths))
    for r in cells:
        print(" | ".join(pad(c, w) for c, w in zip(r, widths)))
    more = " (더 있음 · LIMIT 로 줄여 보세요)" if len(rows) > MAX_ROWS else ""
    print(f"({len(cells)}행{more})")


def run(conn, sql):
    try:
        cur = conn.execute(sql)
        show(cur)
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ {type(e).__name__}: {e}")


def main():
    conn = sqlite3.connect(DB_PATH)
    if len(sys.argv) > 1:
        run(conn, " ".join(sys.argv[1:]))
    else:
        print(f"{DB_PATH.name} 에 연결됨. SQL 을 입력하세요 (빈 줄 = 종료)")
        while True:
            sql = input("sql> ").strip()
            if not sql:
                break
            run(conn, sql)
    conn.close()


if __name__ == "__main__":
    main()
