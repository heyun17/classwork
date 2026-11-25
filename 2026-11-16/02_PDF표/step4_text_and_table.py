# STEP 4. 표 영역과 나머지 글자를 나눠서 뽑기
import pdfplumber

PDF_PATH = "표샘플_어려움.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[0]
    tables = page.find_tables()

    # ① 그냥 extract_text: 표 안 글자까지 본문에 섞임
    print("[① 전체 글자 앞부분]")
    print(page.extract_text()[:260], "...\n")

    # ② 표 영역을 빼고 남은 부분만
    rest = page
    for t in tables:
        rest = rest.outside_bbox(t.bbox)                  # 표 사각형 바깥만 남긴 새 페이지 객체
    print("[② 표를 뺀 본문]")
    print(rest.extract_text())

    # ③ 표 영역만
    inside = page.within_bbox(tables[0].bbox)
    print("\n[③ 표 영역 글자 앞부분]")
    print(inside.extract_text()[:80], "...")
