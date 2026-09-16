"""페퍼로니 연구소 — Flask 서버

실행: python app.py  →  http://127.0.0.1:5000
장별로 읽을 곳
  2장  index · order · done
  3장  order(저장 부분) · orders       + db.py
  5장  dashboard · api_insight        + stats.py, ai.py
  6장  맨 아래 /admin 자리
"""
from flask import Flask, jsonify, redirect, render_template, request, url_for

import ai
import db
import stats
from menu_data import CHANNELS, CRUSTS, MAX_QTY, SIZES, calc_amount

# app.py 가 있는 폴더를 기준으로 templates/ 와 static/ 을 찾습니다.
app = Flask(__name__)


# ── 2장 · 메뉴판 ─────────────────────────────────────
@app.route("/")
def index():
    menus = db.get_menus()
    return render_template("index.html", menus=menus)


# ── 2장 · 주문서(GET) / 3장 · 주문 저장(POST) ───────────────
@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "GET":
        selected = request.args.get("menu_id", type=int)     # /order?menu_id=6
        return render_template("order.html", menus=db.get_menus(), crusts=CRUSTS,
                               channels=CHANNELS, selected=selected)

    # POST: 폼 값 꺼내기 (모두 글자로 들어오므로 숫자는 type=int)
    menu = db.get_menu(request.form.get("menu_id", type=int))
    size = request.form.get("size")
    crust = request.form.get("crust")
    qty = request.form.get("qty", type=int)
    channel = request.form.get("channel")

    # 검사: 이상한 값이면 주문서로 돌려보내기
    if (menu is None or size not in SIZES or crust not in CRUSTS
            or channel not in CHANNELS or not qty or not 1 <= qty <= MAX_QTY):
        return redirect(url_for("order"))

    amount = calc_amount(menu, size, crust, qty)             # 금액은 서버가 계산
    order_id = db.add_order(menu["id"], size, crust, qty, channel, amount)   # 3장: 저장
    return redirect(url_for("done", order_id=order_id))       # 저장 후 영수증으로 이동


# ── 2장 · 영수증 ─────────────────────────────────────
@app.route("/done/<int:order_id>")
def done(order_id):
    saved = db.get_order(order_id)
    if saved is None:
        return redirect(url_for("index"))
    return render_template("done.html", order=saved)


# ── 3장 · 주문 내역 ───────────────────────────────────
@app.route("/orders")
def orders():
    channel = request.args.get("channel", "")                 # /orders?channel=배달
    if channel not in CHANNELS:
        channel = ""
    rows = db.get_orders(channel or None, limit=50)
    total = db.count_orders(channel or None)
    return render_template("orders.html", orders=rows, total=total,
                           channel=channel, channels=CHANNELS)


# ── 5장 · 매출 대시보드 ────────────────────────────────
PERIODS = {1: "하루", 7: "7일", 30: "30일"}


@app.route("/dashboard")
def dashboard():
    days = request.args.get("days", 7, type=int)
    if days not in PERIODS:
        days = 7
    s = stats.summary(days)
    return render_template("dashboard.html", s=s, days=days, periods=PERIODS,
                           has_key=ai.has_key(), model=ai.MODEL)


# ── 5장 · AI 인사이트 (JSON API) ─────────────────────────
@app.route("/api/insight", methods=["POST"])
def api_insight():
    body = request.get_json(silent=True) or {}
    days = body.get("days", 7)
    if days not in PERIODS:
        days = 7
    summary_text = stats.to_text(stats.summary(days))   # ① DB 집계 → 요약문
    result = ai.get_insight(summary_text)               # ② 요약문 → AI
    result["summary"] = summary_text                    # 화면에서 “AI에게 보낸 내용” 보여주기
    return jsonify(result)                              # ③ JSON 으로 응답


# ── 6장 · 관리자 대시보드 자리 ───────────────────────────
# 작업지시서(docs/)를 GPT에게 주고 받은 /admin 코드를 여기에 붙입니다.


if __name__ == "__main__":
    # host="0.0.0.0": 나중에 서버로 옮겨도 같은 코드
    # debug=True    : 저장하면 자동 재시작 + 자세한 오류 화면 (개발할 때만)
    app.run(host="0.0.0.0", port=5000, debug=True)
