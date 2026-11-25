"""운영 1 · 임베딩 캐시 — 바뀐 조각만 다시 임베딩하기
사용 예) python m4_ops_cache.py                     # 지금 조각 196 + 질문 7이 캐시에 다 있는지
        python m4_ops_cache.py --simulate          # 정책 문서 하나를 고치고 FAQ 하나를 더했다고 가정 → 무엇을 다시 임베딩하나
        python m4_ops_cache.py --model text-embedding-3-large   # 모델을 바꾸면?
        python m4_ops_cache.py --simulate --apply  # 실제로 바뀐 것만 API로 임베딩해 캐시에 넣기
"""
import argparse

from m4lib import CACHE, EMBED_MODEL, cache_key, embed_with_cache, load_cache, load_chunks, questions, seed_cache_from_embeddings

ap = argparse.ArgumentParser()
ap.add_argument("--simulate", action="store_true")
ap.add_argument("--model")
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()

if not (CACHE / "vectors.npz").exists():
    c = seed_cache_from_embeddings()
    print(f"캐시를 처음 만듭니다: embeddings.npz의 벡터 {len(c)}개를 내용 해시로 저장 → outputs_m4/cache/vectors.npz\n")

chunks = load_chunks()
items = [(c["chunk_id"], c["text"]) for c in chunks] + [(q["id"], q["question"]) for q in questions()]
if a.simulate:
    items = [(i, t + " 단, 2026-11-15 시행 정책은 시행일 이후 주문에만 적용한다." if i == "POL-VER-001#2" else t) for i, t in items]
    items.append(("FAQ-101#1", "질문: 제주 냉장식품을 받고 50시간 뒤에 변질을 알리면 환불되나요?\n답변: 수령 후 48시간이 지나 접수 기한을 넘겼으므로 원칙적으로 품질 예외 환불 대상이 아닙니다."))
    print("가정: POL-VER-001#2 조각에 문장 하나 추가 · FAQ-101 새로 추가\n")

model = a.model or EMBED_MODEL
print(f"모델 {model} · 캐시에 저장된 벡터 {len(load_cache())}개")
print(f"예: {items[0][0]} → 열쇠 {cache_key(items[0][1], model)}\n")
_, st = embed_with_cache([t for _, t in items], apply=a.apply, model=model)
print(f"전체 {st['total']}개 · 캐시 적중 {st['hit']}개 · 새로 임베딩할 것 {len(st['miss'])}개")
for i in st["miss"][:10]:
    print(f"   - {items[i][0]}  ({len(items[i][1])}자)")
if len(st["miss"]) > 10:
    print(f"   … 외 {len(st['miss']) - 10}개")
chars = sum(len(items[i][1]) for i in st["miss"])
print(f"새로 보낼 글자 {chars:,}자" + (f" · 사용 토큰 {st['tokens']}" if a.apply else " · (--apply를 붙이면 이것만 API로 보냄)"))
