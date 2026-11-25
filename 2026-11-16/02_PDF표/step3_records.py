# STEP 3. 표를 dict 리스트로 바꾸고 숫자로 변환 → JSON, CSV 저장
import csv
import json
import pdfplumber

PDF_PATH = "표샘플_쉬움.pdf"


def to_number(text: str):
    """'1,204' → 1204, '88.1' → 88.1, 숫자가 아니면 원래 글자 그대로"""
    cleaned = text.replace(",", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        pass
    try:
        return float(cleaned)
    except ValueError:
        return text


with pdfplumber.open(PDF_PATH) as pdf:
    rows = pdf.pages[0].extract_tables()[0]               # 첫 번째 표 (리스트의 리스트)

header, *body = rows                                       # 첫 행 = 머리글, 나머지 = 본문
records = [dict(zip(header, map(to_number, row))) for row in body]

print("머리글:", header)
for r in records[:3]:
    print(r)
print("...")
print("합계 행:", records[-1])

# 검증: 기관별 신청 건수를 더하면 합계와 같아야 함
total = sum(r["신청 건수"] for r in records if r["기관 유형"] != "합계")
print(f"\n검증: 신청 건수 합 {total} / 표의 합계 {records[-1]['신청 건수']} → {'OK' if total == records[-1]['신청 건수'] else '불일치'}")

with open("easy_table.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

with open("easy_table.csv", "w", encoding="utf-8-sig", newline="") as f:   # utf-8-sig: 엑셀에서 한글 안 깨짐
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(records)
print("easy_table.json, easy_table.csv 저장")
