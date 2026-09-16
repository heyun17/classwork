"""환경 점검 (1장)  실행: python check_env.py"""
import os
import sqlite3
import sys
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).parent
WANT = {"python": "3.12.10", "flask": "3.1.3",
        "openai": "3.14.0", "python-dotenv": "1.2.3"}

now = {"python": sys.version.split()[0]}
for pkg in ["flask", "openai", "python-dotenv"]:
    now[pkg] = version(pkg)

ok = True
for name, want in WANT.items():
    good = now[name] == want
    ok = ok and good
    mark = "✅" if good else "❌"
    print(f"{mark} {name:14} 기대 {want:8} 현재 {now[name]}")

# .env 의 키 (값은 화면에 찍지 않음)
load_dotenv(HERE / ".env")
key = os.getenv("OPENAI_API_KEY", "")
model = os.getenv("OPENAI_MODEL") or "gpt-5.6-luna"
if key.startswith("sk-"):
    print(f"✅ API 키        {len(key)}자 · 모델 {model}")
else:
    print("⚠ API 키        없음 — 4장 전까지 넣으면 됩니다")

# shop.db
db = HERE / "shop.db"
if db.exists():
    conn = sqlite3.connect(db)
    n = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    sql = "SELECT MAX(ordered_at) FROM orders"
    last = conn.execute(sql).fetchone()[0]
    conn.close()
    print(f"✅ shop.db       주문 {n:,}건 · 마지막 {last}")
else:
    ok = False
    print("❌ shop.db       없음 — tools/make_shop_db.py 실행")

print("가상환경 위치:", sys.prefix)
print("🍕 주방 준비 완료!" if ok else "⚠ ❌ 항목을 확인하세요")
