# STEP 6. 두 쪽에 걸친 표 이어 붙이기 (어려운 샘플 · 표 2)
import json
import pdfplumber

PDF_PATH = "표샘플_어려움.pdf"

pieces = []                                                # (쪽 번호, 표) 모음
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            pieces.append((page.page_number, table))       # page_number는 1부터

print("쪽별로 찾은 표:")
for page_no, table in pieces:
    print(f"  {page_no}쪽: {len(table)}행 x {len(table[0])}열, 첫 행 = {table[0][:3]}")

# 머리글이 같은 표 조각끼리 이어 붙이기
merged = {}                                                # 머리글(튜플) → 행 리스트
for page_no, table in pieces:
    key = tuple(table[0])                                  # 리스트는 dict 키가 안 되므로 튜플로
    if key in merged:
        merged[key]["rows"].extend(table[1:])              # 반복된 머리글은 빼고 본문만 추가
        merged[key]["pages"].append(page_no)
    else:
        merged[key] = {"rows": table[1:], "pages": [page_no]}

header = ("번호", "분류", "기법", "설명", "재식별\n위험", "유용성")
technique = merged[header]
print(f"\n표 2: {technique['pages']}쪽에 걸쳐 본문 {len(technique['rows'])}행")

clean = lambda c: (c or "").replace("\n", " ")             # 칸 안 줄바꿈 → 공백
names = [clean(h) for h in header]
records = [dict(zip(names, map(clean, row))) for row in technique["rows"]]

numbers = [int(r["번호"]) for r in records]
print("번호가 1부터 빠짐없이 이어지나:", numbers == list(range(1, len(numbers) + 1)))
print("셀 안 줄바꿈 정리 예:", records[3]["기법"], "/", records[6]["설명"])

with open("hard_table2.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print("hard_table2.json 저장")
