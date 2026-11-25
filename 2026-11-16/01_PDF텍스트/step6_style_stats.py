# STEP 6. 서식별로 글자 수 세기 → 본문 서식 찾기
import json
from collections import Counter

with open("spans.json", encoding="utf-8") as f:   # STEP 5에서 만든 파일
    spans = json.load(f)


def style_key(s: dict) -> tuple:
    """같은 서식인지 비교할 기준: (크기, 굵기, 색)"""
    return (s["size"], s["bold"], s["color"])


chars = Counter()                                 # 서식별 글자 수
examples = {}                                     # 서식별 예시 문장
for s in spans:
    key = style_key(s)
    chars[key] += len(s["text"])
    examples.setdefault(key, s["text"].strip()[:22])      # 처음 본 서식이면 예시 저장

print(f"{'크기':>5} {'굵게':>4} {'색':>8} {'글자 수':>6}  예시")
for (size, bold, color), n in chars.most_common():
    print(f"{size:>5} {str(bold):>5} {color:>8} {n:>7}  {examples[(size, bold, color)]}")

body_size, body_bold, body_color = chars.most_common(1)[0][0]
print(f"\n▶ 본문 서식 = 크기 {body_size}, 굵게 {body_bold}, 색 {body_color}  (글자가 가장 많은 서식)")
