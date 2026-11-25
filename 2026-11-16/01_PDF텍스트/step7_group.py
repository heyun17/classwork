# STEP 7. 같은 서식이 이어지는 줄끼리 묶기
import json
from itertools import groupby

with open("spans.json", encoding="utf-8") as f:
    spans = json.load(f)

def join_spans(group: list[dict]) -> str:
    """span을 이어 붙이되, 사이가 2pt 넘게 떨어져 있으면 띄어쓰기를 넣음"""
    text = group[0]["text"]
    for prev, cur in zip(group, group[1:]):          # (앞 span, 뒤 span) 짝으로 순회
        gap = cur["bbox"][0] - prev["bbox"][2]       # 뒤 span 왼쪽 x - 앞 span 오른쪽 x
        need_space = gap > 2 and not text.endswith(" ") and not cur["text"].startswith(" ")
        text += (" " if need_space else "") + cur["text"]
    return text.strip()


def union(boxes: list[list]) -> list:
    """여러 사각형을 모두 감싸는 사각형 [x0, y0, x1, y1]"""
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


# ① span → 줄(line): 같은 쪽·블록·줄 번호인 span을 합침
lines = []
for (page, block, line), group in groupby(spans, key=lambda s: (s["page"], s["block"], s["line"])):
    group = list(group)                                         # groupby 결과는 한 번만 읽을 수 있어 list로
    main = max(group, key=lambda s: len(s["text"]))             # 글자가 가장 많은 span = 그 줄의 대표 서식
    lines.append({
        "page": page,
        "text": join_spans(group),
        "size": main["size"], "bold": main["bold"], "color": main["color"],
        "y": group[0]["bbox"][1],                               # 줄의 위쪽 좌표
        "bbox": union([s["bbox"] for s in group]),
    })

# ② 줄 → 묶음(group): 서식이 같은 줄이 연달아 나오면 하나로 합침
style = lambda ln: (ln["page"], ln["size"], ln["bold"], ln["color"])
groups = []
for key, run in groupby(lines, key=style):
    run = list(run)
    page, size, bold, color = key
    groups.append({
        "page": page, "size": size, "bold": bold, "color": color,
        "y": run[0]["y"], "n_lines": len(run),
        "bbox": union([ln["bbox"] for ln in run]),
        "text": " ".join(ln["text"] for ln in run),
    })

with open("groups.json", "w", encoding="utf-8") as f:
    json.dump(groups, f, ensure_ascii=False, indent=2)

print(f"span {len(spans)}개 → 줄 {len(lines)}개 → 묶음 {len(groups)}개 (groups.json)\n")
for g in groups[:14]:                                           # 1쪽 앞부분 미리 보기
    print(f"p{g['page']} {g['size']:>4} {'B' if g['bold'] else '-'} {g['color']}  "
          f"({g['n_lines']}줄) {g['text'][:40]}")
