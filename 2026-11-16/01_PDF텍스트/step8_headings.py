# STEP 8. 서식 규칙으로 역할을 붙이고, 제목 기준으로 자료 나누기
import json
from collections import Counter

with open("groups.json", encoding="utf-8") as f:   # STEP 7에서 만든 파일
    groups = json.load(f)

# 본문 크기 = 글자 수가 가장 많은 크기 (STEP 6과 같은 방법)
size_chars = Counter()
for g in groups:
    size_chars[g["size"]] += len(g["text"])
BODY_SIZE = size_chars.most_common(1)[0][0]


def classify(g: dict) -> str:
    """서식과 위치로 역할 정하기 (위에서부터 검사해서 먼저 맞는 규칙이 이김)"""
    if g["y"] < 60:                               # 쪽 맨 위 = 머리말
        return "header_footer"
    if g["size"] >= 20:                           # 가장 큰 글자 = 장 제목
        return "title"
    if g["bold"] and g["size"] > BODY_SIZE:       # 본문보다 크고 굵음 = 절 제목
        return "heading"
    if g["color"] == "#ffffff":                   # 흰 글자 = 색 띠 위의 박스 제목
        return "box_title"
    if g["size"] < BODY_SIZE - 1:                 # 본문보다 작음 = 참고·주석
        return "note"
    return "body"                                 # 나머지는 본문


for g in groups:
    g["role"] = classify(g)
print("역할별 개수:", dict(Counter(g["role"] for g in groups)))
with open("roles.json", "w", encoding="utf-8") as f:   # 역할을 붙인 묶음 (STEP 9에서 사용)
    json.dump(groups, f, ensure_ascii=False, indent=2)

# ── 제목을 만날 때마다 새 섹션을 시작 ──
doc_title, number, sections, current = None, "", [], None
for g in groups:
    role, text = g["role"], g["text"]
    if role == "header_footer":
        continue                                  # 머리말은 버림
    if role == "title":
        doc_title = text
    elif role == "heading" and text.isdigit():
        number = text                             # 번호 배지("1")는 기억해 뒀다가 다음 제목 앞에 붙임
    elif role == "heading":
        current = {"chapter": doc_title, "heading": f"{number} {text}".strip(),
                   "pages": [g["page"]], "content": []}
        sections.append(current)
        number = ""
    elif current is not None:                     # 본문·주석·박스 제목은 현재 섹션에 담음
        current["content"].append({"role": role, "page": g["page"], "text": text})
        if g["page"] not in current["pages"]:
            current["pages"].append(g["page"])

with open("sections.json", "w", encoding="utf-8") as f:
    json.dump(sections, f, ensure_ascii=False, indent=2)

# ── 목차처럼 출력 ──
print(f"\n{doc_title}")
for sec in sections:
    roles = Counter(c["role"] for c in sec["content"])
    chars = sum(len(c["text"]) for c in sec["content"])
    print(f"  {sec['heading']:<12} p.{sec['pages']}  본문 {roles['body']} · 주석 {roles['note']} · {chars}자")
    for c in sec["content"]:
        if c["role"] == "box_title":
            print(f"      └ [박스] {c['text']} (p.{c['page']})")
