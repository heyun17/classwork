# STEP 5. 병합 셀 채우기와 2단 머리글 합치기 (어려운 샘플 · 표 1)
import json
import pdfplumber

PDF_PATH = "표샘플_어려움.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[0]
    rows = page.extract_tables()[0]                        # 1쪽 첫 번째 표
    page.to_image(resolution=110).debug_tablefinder().save("debug_hard_p1.png")

print("[원본 추출 결과] None = 병합되어 비어 있는 칸")
for row in rows[:4]:
    print(row)


def fill_right(row: list) -> list:
    """가로 병합(colspan): None이면 왼쪽 칸 값을 이어받음"""
    filled, prev = [], None
    for cell in row:
        if cell is None:
            cell = prev
        filled.append(cell)
        prev = cell
    return filled


def fill_down(rows: list[list], col: int) -> list[list]:
    """세로 병합(rowspan): col번째 칸이 None이면 위 행 값을 이어받음"""
    prev = None
    for row in rows:
        if row[col] is None:
            row[col] = prev
        prev = row[col]
    return rows


def clean(cell) -> str:
    """칸 안의 줄바꿈을 공백으로, None은 빈 문자열로"""
    return (cell or "").replace("\n", " ").strip()


# ① 2단 머리글 → 한 줄 머리글
top = fill_right(rows[0])                                  # ['기관 구분', '세부 유형', '2024년', '2024년', '2025년', '2025년', '비고']
sub = rows[1]                                              # [None, None, '상반기', '하반기', '상반기', '하반기', None]
header = [f"{t}_{s}" if s else t for t, s in zip(top, sub)]
print("\n합친 머리글:", header)

# ② 본문: 첫 칸(기관 구분)은 위에서 채우고, '합계' 행의 가로 병합은 오른쪽으로 채움
body = fill_down([list(r) for r in rows[2:]], col=0)       # list(r): 원본을 건드리지 않게 복사
body = [fill_right(r) if r[1] is None else r for r in body]
records = [dict(zip(header, map(clean, r))) for r in body]

print("\n[정리된 행]")
for r in records:
    print(f"{r['기관 구분']:<6} | {r['세부 유형']:<7} | 2025 상반기 {r['2025년_상반기']:>6} | 비고: {r['비고']}")

with open("hard_table1.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print("\nhard_table1.json 저장")
