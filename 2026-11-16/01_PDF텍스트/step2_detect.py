# STEP 2. 쪽마다 어떤 객체(텍스트·그림·도형·표)가 있는지 탐지
import pymupdf

PDF_PATH = "가이드라인_발췌.pdf"
doc = pymupdf.open(PDF_PATH)

print("쪽 | 텍스트블록 | 그림블록 | 그림파일 | 도형 | 표")
print("-" * 46)
for page in doc:
    blocks = page.get_text("dict")["blocks"]              # 쪽의 모든 블록 (텍스트 + 그림)
    n_text = sum(1 for b in blocks if b["type"] == 0)     # type 0 = 텍스트 블록
    n_img = sum(1 for b in blocks if b["type"] == 1)      # type 1 = 그림 블록 (화면에 놓인 횟수)
    images = page.get_images(full=True)                   # 쪽이 쓰는 그림 파일 (중복 없이)
    drawings = page.get_drawings()                        # 선·사각형 같은 벡터 도형
    tables = page.find_tables().tables                    # 표 탐지 결과 (Table 객체 리스트)
    print(f"{page.number + 1:>2} | {n_text:>10} | {n_img:>8} | {len(images):>8} | {len(drawings):>4} | {len(tables):>2}")

# ── 그림 블록을 크기로 분류해 보기 (4쪽) ──
page = doc[3]
print("\n[4쪽 그림 블록]")
for b in page.get_text("dict")["blocks"]:
    if b["type"] != 1:
        continue
    x0, y0, x1, y1 = b["bbox"]
    w, h = x1 - x0, y1 - y0
    kind = "아이콘" if w < 20 else "박스 조각"            # 폭이 20pt보다 좁으면 아이콘으로 판단
    print(f"  {kind:<5} 위치=({x0:.0f},{y0:.0f}) 크기={w:.0f}x{h:.0f}pt  원본={b['width']}x{b['height']}px  형식={b['ext']}")
