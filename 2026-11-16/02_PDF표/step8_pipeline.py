# STEP 8. 두 샘플의 모든 표를 제목과 함께 한 번에 뽑기
import json
import re
import pdfplumber

FILES = ["표샘플_쉬움.pdf", "표샘플_어려움.pdf"]
TITLE = re.compile(r"^(표\s*\d+\.|\d+\.)\s*\S")            # '표 1. …' 또는 '1. …'로 시작하는 줄
TEXT_SETTINGS = {"vertical_strategy": "text", "horizontal_strategy": "text"}


def find_title(page, top: float):
    """표 위쪽 80pt 안에서 제목처럼 생긴 줄을 아래에서부터 찾음"""
    above = page.crop((0, max(0, top - 80), page.width, top)).extract_text()
    for line in reversed(above.splitlines()):
        if TITLE.match(line.strip()):
            return line.strip()
    return None


def clean_rows(rows: list[list]) -> list[list]:
    rows = [[(c or "").replace("\n", " ").strip() for c in row] for row in rows]
    return [row for row in rows if any(row)]                # 빈 행 제거


def extract_all(path: str) -> list[dict]:
    results = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            found = [(t.bbox, t.extract()) for t in page.find_tables()]
            if not found:                                   # 선으로 못 찾으면 글자 배치로 한 번 더
                t = page.find_table(TEXT_SETTINGS)
                if t is not None:
                    found = [(t.bbox, t.extract())]
            for bbox, rows in found:
                rows = clean_rows(rows)
                title = find_title(page, bbox[1])
                prev = results[-1] if results else None
                # 제목이 없고 머리글이 앞 표와 같으면 = 앞 쪽에서 이어지는 표
                if title is None and prev and prev["header"] == rows[0]:
                    prev["rows"].extend(rows[1:])
                    prev["pages"].append(page.page_number)
                    continue
                results.append({"file": path, "title": title, "pages": [page.page_number],
                                "header": rows[0], "rows": rows[1:]})
    return results


if __name__ == "__main__":
    all_tables = [t for path in FILES for t in extract_all(path)]
    for t in all_tables:
        print(f"[{t['file']}] {t['title']}  쪽 {t['pages']}  {len(t['rows'])}행 x {len(t['header'])}열")
        print("    머리글:", t["header"])
    with open("tables.json", "w", encoding="utf-8") as f:
        json.dump(all_tables, f, ensure_ascii=False, indent=2)
    print("tables.json 저장")
