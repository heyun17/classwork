# STEP 7. 세로선이 없는 표 찾기 (어려운 샘플 · 표 3)
import pdfplumber

PDF_PATH = "표샘플_어려움.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[2]                                    # 3쪽

    # ① 기본 설정(선 기준): 세로선이 없어 표를 못 찾음
    print("① 기본 설정으로 찾은 표:", len(page.find_tables()))

    # ② 글자 배치 기준으로 찾기
    settings = {
        "vertical_strategy": "text",                       # 세로 경계 = 글자들이 세로로 정렬된 위치
        "horizontal_strategy": "text",                     # 가로 경계 = 글자 줄의 위치
    }
    table = page.find_table(settings)                      # 가장 큰 표 하나 (없으면 None)
    rows = table.extract()
    print(f"② text 전략: {len(rows)}행")
    for row in rows[:4]:
        print("  ", row)

    # ③ 빈 행 걸러 내기
    rows = [row for row in rows if any(cell for cell in row)]
    print(f"③ 빈 행 제거 후: {len(rows)}행")
    for row in rows:
        print("  ", row)

    # ④ 디버그 그림: 기본(선) 전략과 text 전략 비교
    page.to_image(resolution=110).debug_tablefinder().save("debug_hard_p3_lines.png")
    page.to_image(resolution=110).debug_tablefinder(settings).save("debug_hard_p3_text.png")
    print("debug_hard_p3_lines.png, debug_hard_p3_text.png 저장")
