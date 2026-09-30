"""sales.csv를 읽어 집계 결과를 JSON으로 돌려주는 아주 작은 API 서버.

외부 라이브러리 없이 파이썬 표준 기능만 쓴다.
  GET /api/summary  -> 집계 결과(JSON)
  GET /api/health   -> 살아 있는지 확인
"""
import csv
import json
import os
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer

CSV_PATH = os.environ.get("CSV_PATH", "sales.csv")
PORT = int(os.environ.get("PORT", "5000"))


def load_summary():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            amount = int(row["quantity"]) * int(row["price"])
            rows.append({**row, "amount": amount})

    by_region = defaultdict(int)
    by_product = defaultdict(int)
    for row in rows:
        by_region[row["region"]] += row["amount"]
        by_product[row["product"]] += row["amount"]

    total = sum(r["amount"] for r in rows)
    return {
        "count": len(rows),
        "total": total,
        "by_region": [{"name": k, "amount": v} for k, v in sorted(by_region.items(), key=lambda x: -x[1])],
        "by_product": [{"name": k, "amount": v} for k, v in sorted(by_product.items(), key=lambda x: -x[1])],
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")   # 브라우저에서 부를 수 있게
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/health"):
            self._send({"status": "ok"})
        elif self.path.startswith("/api/summary"):
            try:
                self._send(load_summary())
            except FileNotFoundError:
                self._send({"error": f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}"}, 500)
        else:
            self._send({"error": "not found", "try": ["/api/summary", "/api/health"]}, 404)

    def log_message(self, fmt, *args):
        print(f"[api] {self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"[api] CSV_PATH={CSV_PATH}  PORT={PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
