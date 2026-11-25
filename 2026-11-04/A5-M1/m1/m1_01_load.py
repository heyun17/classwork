"""실습 01 · 자료 로딩 — CSV(FAQ)와 마크다운(정책)을 같은 모양의 문서로 읽는다."""
from m1lib import DATA, load_faq, load_policies, read_csv

faq, pol = load_faq(), load_policies()
print(f"FAQ {len(faq)}개 · 정책 {len(pol)}개 · 합계 {len(faq) + len(pol)}개\n")

print("[FAQ 문서 하나]")
d = faq[0]
print(f"  id    : {d['id']}\n  kind  : {d['kind']}\n  text  : {d['text']!r}\n  meta  : {d['meta']}\n  links : {d['links']}\n")

print("[정책 문서 하나]")
d = next(x for x in pol if x["id"] == "POL-RET-002")
print(f"  id    : {d['id']}\n  kind  : {d['kind']}\n  title : {d['title']}\n  meta  : {d['meta']}")
print(f"  text  : {len(d['text'])}자, 처음 3줄 → {d['text'].splitlines()[:3]}\n")

print("[목록과 파일이 맞는가]")
rows = read_csv(DATA / "policies.csv")
missing = [r["file"] for r in rows if not (DATA / r["file"]).exists()]
extra = sorted({p.name for p in (DATA / "md").glob("*.md")} - {r["file"].split("/")[-1] for r in rows})
print(f"  policies.csv {len(rows)}행 · 링크된 파일이 없는 행 {missing or '없음'} · 목록에 없는 md 파일 {extra or '없음'}")
