# STEP 1. 표 찾기 (쉬운 샘플)
import pdfplumber

PDF_PATH = "표샘플_어려움.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[0]                                   # 1쪽 (0부터)
    print("쪽 크기:", page.width, "x", page.height)
    print("선(line) 개수:", len(page.lines), "/ 사각형(rect) 개수:", len(page.rects))

    tables = page.find_tables()                           # Table 객체 리스트
    print("찾은 표:", len(tables), "개")

    table = tables[0]
    x0, top, x1, bottom = table.bbox                      # 표를 감싸는 사각형
    print(f"표 위치: x {x0:.0f}~{x1:.0f}, y {top:.0f}~{bottom:.0f}")
    print("행 수:", len(table.rows), "/ 칸(cell) 수:", len(table.cells))

    rows = table.extract()                                # [[칸, 칸, ...], [칸, ...], ...]
    print("\n[추출 결과]")
    for i, row in enumerate(rows):
        print(i, row)
