# STEP 9. 역할 판정 결과를 쪽 그림 위에 색으로 칠해 눈으로 검증하기
import json
import pymupdf

PDF_PATH = "가이드라인_발췌.pdf"
ROLE_COLORS = {                                   # 역할 → 색 (RGB 0~1)
    "header_footer": (0.6, 0.6, 0.6),
    "title":         (0.55, 0.1, 0.75),
    "heading":       (0.9, 0.1, 0.1),
    "box_title":     (1.0, 0.55, 0.0),
    "body":          (0.1, 0.4, 1.0),
    "note":          (0.1, 0.65, 0.3),
}

with open("roles.json", encoding="utf-8") as f:   # STEP 8에서 만든 파일
    groups = json.load(f)

with pymupdf.open(PDF_PATH) as doc:
    for page_no in (1, 4):                        # 1쪽, 4쪽
        page = doc[page_no - 1]
        for g in (g for g in groups if g["page"] == page_no):
            rect = pymupdf.Rect(g["bbox"]) + (-2, -2, 2, 2)          # 사방으로 2pt 넓힘
            color = ROLE_COLORS[g["role"]]
            page.draw_rect(rect, color=color, fill=color, fill_opacity=0.12, width=1.2)
            page.insert_text((rect.x1 + 3, rect.y0 + 7), g["role"], fontsize=6, color=color)
        page.get_pixmap(dpi=110).save(f"roles_p{page_no}.png")
        print(f"roles_p{page_no}.png 저장")
