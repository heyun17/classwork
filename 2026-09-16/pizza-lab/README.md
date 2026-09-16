# 🍕 페퍼로니 연구소 — Flask + SQLite + OpenAI

피자 가게 주문을 받고(Flask), 저장하고(SQLite), 대시보드로 보여주고, AI가 조언하는 완성 프로젝트입니다.

## 실행
```bash
python -m venv .venv
.venv\Scripts\activate            # macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
copy .env.example .env            # macOS: cp .env.example .env  → 키 입력
python check_env.py
python app.py                     # http://127.0.0.1:5000
```
샘플 주문을 오늘 날짜 기준으로 새로 만들려면: `python tools/make_shop_db.py`
DB에 SQL을 직접 실행하려면: `python tools/sql.py "SELECT * FROM menus"`

## 장별로 읽을 파일
| 장 | 주제 | 파일 |
|---|---|---|
| 1 | 개요 · 세팅 | README.md, requirements.txt, check_env.py, .env.example |
| 2 | Flask와 HTML | app.py (index · order · done), menu_data.py, templates/base·index·order·done.html |
| 3 | DB 저장·조회 | db.py, app.py (order 저장 · orders), templates/orders.html, shop.db, tools/sql.py |
| 4 | OpenAI 호출 | ai.py, ai_test.py |
| 5 | 대시보드 + AI | stats.py, app.py (dashboard · api_insight), templates/dashboard.html |
| 6 | GPT로 관리자 화면 | docs/admin_작업지시서_템플릿.md, app.py 맨 아래 /admin 자리 |

## 주소
| 주소 | 방식 | 하는 일 |
|---|---|---|
| `/` | GET | 메뉴판 |
| `/order` | GET · POST | 주문서 · 주문 저장 |
| `/done/<번호>` | GET | 영수증 |
| `/orders` | GET | 주문 내역 (`?channel=배달`) |
| `/dashboard` | GET | 매출 대시보드 (`?days=1·7·30`) |
| `/api/insight` | POST | 집계 요약 → AI 조언 (JSON) |
