# STEP 4. 텍스트 블록 안을 들여다보기: block → line → span
import pymupdf

PDF_PATH = "가이드라인_발췌.pdf"
doc = pymupdf.open(PDF_PATH)
page = doc[0]

data = page.get_text("dict")                     # dict 모드: 서식 정보까지 포함
print("dict의 키 :", list(data.keys()))

text_blocks = [b for b in data["blocks"] if b["type"] == 0]   # 텍스트 블록만 골라냄

# "필요성"이라는 글자가 들어 있는 블록 찾기 (next: 조건에 맞는 첫 번째 것)
block = next(
    b for b in text_blocks
    if any("필요성" in s["text"] for line in b["lines"] for s in line["spans"])
)
print("block의 키:", list(block.keys()), "/ line 수:", len(block["lines"]))
print("line의 키 :", list(block["lines"][0].keys()))


def flags_to_style(flags: int) -> dict:
    """flags 숫자(비트)를 사람이 읽을 수 있는 서식으로 바꿈"""
    return {
        "superscript": bool(flags & 1),          # 비트 0 (1)
        "italic":      bool(flags & 2),          # 비트 1 (2)
        "serif":       bool(flags & 4),          # 비트 2 (4)
        "monospace":   bool(flags & 8),          # 비트 3 (8)
        "bold":        bool(flags & 16),         # 비트 4 (16)
    }


for l_no, line in enumerate(block["lines"]):     # enumerate: (번호, 값)을 함께 꺼냄
    for span in line["spans"]:
        print(f"\n[line {l_no}] span 정보")
        for key in ("text", "font", "size", "flags", "color", "bbox"):
            print(f"  {key:<5} = {span[key]}")
        style = {k: v for k, v in flags_to_style(span["flags"]).items() if v}   # True인 것만
        print(f"  → 서식: {style}, 색: #{span['color']:06x}")
