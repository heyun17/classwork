import os
from datetime import datetime

import pandas as pd

# 경로는 밖에서 바꿀 수 있게 (기본값은 컨테이너 기준)
CSV_PATH = os.environ.get("CSV_PATH", "/data/sales.csv")
OUT_PATH = os.environ.get("OUT_PATH", "/out/report.html")

# 1) 데이터 읽기
df = pd.read_csv(CSV_PATH)

# 2) 매출 계산
df["amount"] = df["quantity"] * df["price"]

# 3) 집계
by_region = df.groupby("region")["amount"].sum().sort_values(ascending=False)
by_product = df.groupby("product")["amount"].sum().sort_values(ascending=False)

# 4) HTML 조립
html = f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><title>매출 리포트</title></head>
<body>
<h1>매출 리포트</h1>
<p>생성 시각 : {datetime.now():%Y-%m-%d %H:%M:%S}</p>
<p>총 매출 : {df['amount'].sum():,}원 (거래 {len(df)}건)</p>

<h2>지역별</h2>
{by_region.to_frame("매출").to_html()}

<h2>제품별</h2>
{by_product.to_frame("매출").to_html()}

<p><a href="index.html">처음으로</a></p>
</body>
</html>"""

# 5) 저장
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"[report] {CSV_PATH} → {OUT_PATH}")
print(f"[report] 총 매출 {df['amount'].sum():,}원 / 거래 {len(df)}건")
print(by_region)
