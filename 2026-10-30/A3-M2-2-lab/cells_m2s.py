# A3-M2-2 FAISS 실전 — 쇼핑몰 FAQ CSV 하나로 검색·메타데이터 필터·RAG 평가·리랭킹
NB1 = [
("d1", "CSV 읽어서 눈으로 보기", '''import pandas as pd
faq = pd.read_csv("shop_faq.csv")
tests = pd.read_csv("shop_faq_tests.csv")
print("FAQ:", faq.shape, "| 평가 질문:", tests.shape)
print(faq.dtypes.to_string())
print()
print(faq.head(5).to_string(index=False))
print()
print(faq["category"].value_counts().to_string())'''),

("d2", "검색에 쓸 문장(doc) 만들기", '''faq["doc"] = faq["question"] + " " + faq["answer"]
print(faq.loc[0, "doc"])
print("doc 글자 수:", faq["doc"].str.len().describe()[["min", "mean", "max"]].round(1).to_dict())'''),

("d3", "Hugging Face 파이프라인 출력 들여다보기", '''import numpy as np
import faiss
from transformers import pipeline
from emb import EMB_MODEL

fe = pipeline("feature-extraction", model=EMB_MODEL, device=-1)
s = "query: 택배 언제 와요?"
out = fe(s)
arr = np.array(out)
print("모델:", EMB_MODEL)
print("출력 모양:", arr.shape, "← 문장 1개 × 토큰 수 × 384")
print("토큰:", fe.tokenizer.tokenize(s))
v = arr[0].mean(axis=0)
print("토큰 평균:", v.shape, "길이", round(float(np.linalg.norm(v)), 3))'''),

("d4", "embed() 함수 만들고 FAQ 20건을 벡터로", '''def embed(texts, kind="passage"):
    outs = fe([f"{kind}: {t}" for t in texts])                       # 문장마다 [1][토큰][384]
    X = np.array([np.array(o[0]).mean(axis=0) for o in outs], dtype="float32")
    faiss.normalize_L2(X)                                              # 길이 1 → 내적 = 코사인
    return X

X = embed(faq["doc"].tolist())
print("X:", X.shape, X.dtype)
print("길이:", np.linalg.norm(X, axis=1).round(3)[:5], "...")
np.save("faq_vectors.npy", X)
print("저장: faq_vectors.npy")'''),

("d5", "FAISS 전에 — 질문 하나와 FAQ 20건 코사인 직접 계산", '''q = embed(["택배 언제 와요?"], kind="query")
sims = X @ q[0]                                   # (20, 384) @ (384,) → (20,)
top = np.argsort(-sims)[:5]
print(faq.loc[top, ["faq_id", "category", "question"]].assign(cosine=sims[top].round(3)).to_string(index=False))'''),
]

PREP2 = '''import json, os
import numpy as np
import pandas as pd
import faiss
from emb import embed, EMB_MODEL

faq = pd.read_csv("shop_faq.csv")
faq["doc"] = faq["question"] + " " + faq["answer"]
X = np.load("faq_vectors.npy")
print("FAQ", len(faq), "건 | 벡터", X.shape)'''

NB2 = [
("s0", "준비 — CSV와 저장한 벡터 불러오기", PREP2),

("s1", "IndexFlatIP 만들고 검색하기", '''index = faiss.IndexFlatIP(X.shape[1])
index.add(X)
print("저장된 개수:", index.ntotal)

q = embed(["택배 언제 와요?"], kind="query")
D, I = index.search(q, 3)
print("D:", D.round(3))
print("I:", I)
print(faq.loc[I[0], ["faq_id", "category", "question"]].assign(score=D[0].round(3)).to_string(index=False))'''),

("s2", "질문 여러 개 · k가 문서 수보다 클 때", '''qs = ["환불 며칠 걸려요?", "포인트 언제 없어져요?"]
D, I = index.search(embed(qs, kind="query"), 2)
for q, d, i in zip(qs, D, I):
    print(q, "→", faq.loc[i, "question"].tolist(), d.round(3).tolist())

D, I = index.search(embed(["환불"], kind="query"), 25)      # FAQ는 20건
print("k=25 마지막 5칸 I:", I[0][-5:].tolist())'''),

("s3", "메타데이터 구조 — faq_id를 FAISS id로", '''ids = faq["faq_id"].to_numpy(dtype="int64")
index = faiss.IndexIDMap2(faiss.IndexFlatIP(X.shape[1]))
index.add_with_ids(X, ids)

meta = faq.set_index("faq_id")                    # id → category, question, answer
D, I = index.search(embed(["택배 언제 와요?"], kind="query"), 3)
print("I:", I)                                    # 이제 FAQ 번호가 나온다
print(meta.loc[I[0], ["category", "question"]].assign(score=D[0].round(3)).to_string())
print("401번 벡터 앞 5칸:", index.reconstruct(401)[:5].round(3))'''),

("s4", "카테고리 필터 — 검색 안에서 거르기", '''def ids_of(categories):
    return meta.index[meta["category"].isin(categories)].to_numpy(dtype="int64")

qv = embed(["돈 언제 돌려줘요?"], kind="query")
for cats in [None, ["환불"], ["환불", "결제"], ["배송"]]:
    params = None if cats is None else faiss.SearchParameters(sel=faiss.IDSelectorBatch(ids_of(cats)))
    D, I = index.search(qv, 3, params=params)
    got = [(int(i), meta.loc[i, "category"], round(float(d), 3)) for d, i in zip(D[0], I[0]) if i != -1]
    print("전체" if cats is None else cats, got)'''),

("s5", "검색 뒤에 거르면 왜 안 되나 · 빼고 찾기", '''D, I = index.search(qv, 3)
after = [int(i) for i in I[0] if meta.loc[i, "category"] == "결제"]
print("검색 후 거르기(결제):", after, "→", len(after), "개")

params = faiss.SearchParameters(sel=faiss.IDSelectorBatch(ids_of(["결제"])))
D, I = index.search(qv, 3, params=params)
print("검색 안에서 거르기(결제):", I[0].tolist())

keep = faiss.IDSelectorBatch(ids_of(["환불"]))
params = faiss.SearchParameters(sel=faiss.IDSelectorNot(keep))      # 환불만 빼고
D, I = index.search(qv, 3, params=params)
print("환불 빼고:", [(int(i), meta.loc[i, "category"]) for i in I[0]])'''),

("s6", "검색 함수 하나로 묶기", '''def search(question, k=3, categories=None):
    params = None
    if categories:
        params = faiss.SearchParameters(sel=faiss.IDSelectorBatch(ids_of(categories)))
    D, I = index.search(embed([question], kind="query"), k, params=params)
    hits = [(int(i), float(d)) for d, i in zip(D[0], I[0]) if i != -1]
    res = meta.loc[[i for i, _ in hits], ["category", "question", "answer"]].copy()
    res.insert(0, "score", [round(s, 3) for _, s in hits])
    return res

print(search("카드 할부 돼요?")[["score", "category", "question"]].to_string())
print()
print(search("카드 할부 돼요?", categories=["결제"])[["score", "category", "question"]].to_string())'''),

("s7", "저장하고 다시 열기 — 인덱스 + 메타데이터 + 설정", '''os.makedirs("faq_store", exist_ok=True)
faiss.write_index(index, "faq_store/index.faiss")
meta.drop(columns="doc").to_csv("faq_store/meta.csv", encoding="utf-8-sig")
manifest = {"model": EMB_MODEL, "dim": int(X.shape[1]), "count": int(index.ntotal), "metric": "cosine(IP)"}
json.dump(manifest, open("faq_store/manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for f in sorted(os.listdir("faq_store")):
    print(f"{f:<14} {os.path.getsize('faq_store/' + f):>7,} bytes")

ix2 = faiss.read_index("faq_store/index.faiss")
meta2 = pd.read_csv("faq_store/meta.csv").set_index("faq_id")
man = json.load(open("faq_store/manifest.json", encoding="utf-8"))
assert man["model"] == EMB_MODEL and ix2.ntotal == len(meta2)
D, I = ix2.search(embed(["반품 기간"], kind="query"), 2)
print("다시 연 인덱스:", I[0].tolist(), meta2.loc[I[0], "question"].tolist())'''),
]

PREP3 = '''import json, time
import numpy as np
import pandas as pd
import faiss
from emb import embed, EMB_MODEL, RERANK_MODEL

index = faiss.read_index("faq_store/index.faiss")
meta = pd.read_csv("faq_store/meta.csv").set_index("faq_id")
man = json.load(open("faq_store/manifest.json", encoding="utf-8"))
assert man["model"] == EMB_MODEL, "다른 모델로 만든 인덱스입니다"
tests = pd.read_csv("shop_faq_tests.csv")

def ids_of(categories):
    return meta.index[meta["category"].isin(categories)].to_numpy(dtype="int64")

def search(question, k=3, categories=None):
    params = None
    if categories:
        params = faiss.SearchParameters(sel=faiss.IDSelectorBatch(ids_of(categories)))
    D, I = index.search(embed([question], kind="query"), k, params=params)
    hits = [(int(i), float(d)) for d, i in zip(D[0], I[0]) if i != -1]
    res = meta.loc[[i for i, _ in hits], ["category", "question", "answer"]].copy()
    res.insert(0, "score", [round(s, 3) for _, s in hits])
    return res

print("FAQ", index.ntotal, "건 | 평가 질문", len(tests), "개 | 모델", man["model"])'''

RR_DEF = '''
from transformers import pipeline
rr = pipeline("text-classification", model=RERANK_MODEL, device=-1)

def search_rerank(question, k=3, pool=8, categories=None):
    cand = search(question, k=pool, categories=categories)              # 1단계: FAISS로 후보
    pairs = [{"text": question, "text_pair": f"{r.question} {r.answer}"} for r in cand.itertuples()]
    cand["rerank"] = [round(s["score"], 3) for s in rr(pairs, function_to_apply="none")]
    return cand.sort_values("rerank", ascending=False).head(k)          # 2단계: 다시 줄 세우기

def evaluate(fn, **kw):
    rows = []
    for q, gold in tests.itertuples(index=False):
        ranked = fn(q, **kw).index.tolist()
        rows.append({"question": q, "gold": gold, "top1": ranked[0],
                     "rank": ranked.index(gold) + 1 if gold in ranked else np.nan})
    return pd.DataFrame(rows)

def summary(ev):
    return {"Hit@1": round((ev["rank"] == 1).mean(), 3), "Hit@3": round((ev["rank"] <= 3).mean(), 3),
            "MRR": round((1 / ev["rank"]).fillna(0).mean(), 3)}'''

NB3 = [
("e0", "준비 — 저장한 검색기 열기", PREP3),

("e1", "평가 질문 12개로 검색 평가 — Hit@1 · Hit@3 · MRR", '''rows = []
for q, gold in tests.itertuples(index=False):
    res = search(q, k=5)
    ranked = res.index.tolist()
    rank = ranked.index(gold) + 1 if gold in ranked else np.nan
    rows.append({"question": q, "gold": gold, "top1": ranked[0], "rank": rank, "top1_score": res["score"].iloc[0]})
ev = pd.DataFrame(rows)
print(ev.assign(rank=ev["rank"].astype("Int64")).to_string(index=False))

hit1 = (ev["rank"] == 1).mean()
hit3 = (ev["rank"] <= 3).mean()
mrr = (1 / ev["rank"]).fillna(0).mean()
print(f"\\nHit@1 {hit1:.3f}  Hit@3 {hit3:.3f}  MRR {mrr:.3f}")'''),

("e2", "틀린 질문 들여다보기", '''miss = ev[ev["rank"] != 1]
print(f"1위가 정답이 아닌 질문 {len(miss)}개")
for r in miss.itertuples(index=False):
    print(f"\\nQ: {r.question}")
    print(f"  정답 {r.gold} [{meta.loc[r.gold, 'category']}] {meta.loc[r.gold, 'question']}  (정답 순위 {r.rank})")
    print(f"  1위  {r.top1} [{meta.loc[r.top1, 'category']}] {meta.loc[r.top1, 'question']}")'''),

("e3", "답하지 않을 기준 정하기 — 점수 분포 보기", '''off = ["오늘 날씨 어때요?", "주식 추천해 주세요", "점심 메뉴 골라줘", "파이썬 설치 방법", "축구 경기 결과 알려줘", "영화 추천해 줘"]
ok = sorted(ev["top1_score"].round(3).tolist())
bad = sorted(round(float(search(q, 1)["score"].iloc[0]), 3) for q in off)
print("쇼핑 질문 1위 점수:", ok)
print("상관없는 질문 점수:", bad)
THRESHOLD = round((min(ok) + max(bad)) / 2, 3)
print("기준값 후보:", THRESHOLD, "| 겹침" if min(ok) <= max(bad) else "| 두 분포가 나뉨")'''),

("e4", "LLM에 넘길 프롬프트 만들기 (RAG의 R까지)", '''def build_prompt(question, k=3, categories=None):
    res = search(question, k, categories)
    if res["score"].iloc[0] < THRESHOLD:
        return None
    ctx = "\\n".join(f"[{i}] ({r.category}) Q: {r.question} A: {r.answer}" for i, r in res.iterrows())
    return f"다음 FAQ만 근거로 답하세요. 답 끝에 근거 번호를 적으세요.\\n\\n{ctx}\\n\\n질문: {question}"

print(build_prompt("물건이 깨져서 왔어요"))
print("\\n오늘 날씨 어때요? →", build_prompt("오늘 날씨 어때요?") or "상담원 연결(근거 부족)")'''),

("r1", "리랭커 써 보기 — 질문과 문서를 한 쌍으로 넣는 모델", '''from transformers import pipeline
rr = pipeline("text-classification", model=RERANK_MODEL, device=-1)

q = "물건이 깨져서 왔어요"
cand = search(q, k=5)
pairs = [{"text": q, "text_pair": f"{r.question} {r.answer}"} for r in cand.itertuples()]
scores = rr(pairs, function_to_apply="none")
print("모델:", RERANK_MODEL)
print("출력 예:", scores[0])
cand["rerank"] = [round(s["score"], 3) for s in scores]
print("\\n[FAISS 순서]")
print(cand[["score", "rerank", "category", "question"]].to_string())
print("\\n[리랭킹 순서]")
print(cand.sort_values("rerank", ascending=False)[["score", "rerank", "category", "question"]].to_string())'''),

("r2", "검색 + 리랭킹 함수로 다시 평가", RR_DEF.replace("from transformers import pipeline\nrr = pipeline(\"text-classification\", model=RERANK_MODEL, device=-1)\n", "") + '''

ev_base = evaluate(search, k=5)
ev_rr = evaluate(search_rerank, k=5, pool=8)
print(pd.DataFrame({"검색만": summary(ev_base), "검색+리랭킹": summary(ev_rr)}).to_string())'''),

("r3", "어떤 질문이 바뀌었나 · 시간은 얼마나 드나", '''both = ev_base[["question", "gold", "rank"]].merge(ev_rr[["question", "rank"]], on="question", suffixes=("_검색", "_리랭킹"))
both["변화"] = np.where(both["rank_리랭킹"] < both["rank_검색"], "↑", np.where(both["rank_리랭킹"] > both["rank_검색"], "↓", ""))
print(both.astype({"rank_검색": "Int64", "rank_리랭킹": "Int64"}).to_string(index=False))

for name, fn in [("검색만", lambda q: search(q, 5)), ("검색+리랭킹", lambda q: search_rerank(q, 5, 8))]:
    t = time.perf_counter()
    for q in tests["question"]:
        fn(q)
    print(f"{name:<8} 질문당 {(time.perf_counter() - t) / len(tests) * 1000:.0f} ms")'''),
]

NOTEBOOKS = [("01_데이터와_임베딩", NB1), ("02_FAISS_검색과_메타데이터", NB2), ("03_RAG평가와_리랭킹", NB3)]

EX = [
("x0", "준비", "모든 과제가 함께 쓰는 준비 셀입니다. 02 노트북을 먼저 실행해 faq_store/가 있어야 합니다.", PREP3 + RR_DEF, None),
("x1", "과제 1 · 카테고리를 알면 얼마나 좋아지나", "평가 질문마다 정답 FAQ의 카테고리로 필터를 걸고(`categories=[...]`) 검색해서, 필터 없을 때와 Hit@1·MRR을 비교하세요. 화면에서 고객이 카테고리를 먼저 고르는 상황입니다.",
'''# TODO''',
'''rows = []
for q, gold in tests.itertuples(index=False):
    cat = meta.loc[gold, "category"]
    ranked = search(q, k=5, categories=[cat]).index.tolist()
    rows.append({"question": q, "gold": gold, "top1": ranked[0], "rank": ranked.index(gold) + 1 if gold in ranked else np.nan})
ev_cat = pd.DataFrame(rows)
print(pd.DataFrame({"필터 없음": summary(evaluate(search, k=5)), "정답 카테고리 필터": summary(ev_cat)}).to_string())'''),
("x2", "과제 2 · 리랭킹 후보 수(pool) 고르기", "`search_rerank`의 `pool`을 3, 5, 8, 20으로 바꿔 Hit@1·MRR과 질문당 시간을 표로 만드세요. 후보가 많을수록 항상 좋은지 확인합니다.",
'''# TODO''',
'''rows = []
for pool in [3, 5, 8, 20]:
    t = time.perf_counter()
    ev = evaluate(search_rerank, k=min(5, pool), pool=pool)
    ms = (time.perf_counter() - t) / len(tests) * 1000
    rows.append({"pool": pool, **summary(ev), "ms/질문": round(ms)})
print(pd.DataFrame(rows).to_string(index=False))'''),
("x3", "과제 3 · 평가 질문 늘리기", "고객이 실제로 쓸 법한 질문 5개를 직접 만들어 정답 FAQ 번호와 함께 `tests`에 추가하고, 검색만/검색+리랭킹 결과를 다시 비교하세요. 평가 질문이 늘면 숫자가 어떻게 바뀌나요?",
'''new = pd.DataFrame([
    # ("질문", 정답 faq_id),
], columns=tests.columns)
# TODO''',
'''new = pd.DataFrame([
    ("주문한 거 없던 걸로 해 주세요", 501), ("로그인 암호가 생각이 안 나요", 601), ("쿠폰이랑 포인트 같이 써도 돼요?", 702),
    ("마음이 바뀌어서 돌려보내면 택배비 내야 해요?", 302), ("현금영수증 받고 싶어요", 203),
], columns=tests.columns)
print(new.assign(faq_question=meta.loc[new["gold_faq_id"], "question"].values).to_string(index=False))
tests = pd.concat([tests, new], ignore_index=True)
print("평가 질문", len(tests), "개")
print(pd.DataFrame({"검색만": summary(evaluate(search, k=5)), "검색+리랭킹": summary(evaluate(search_rerank, k=5, pool=8))}).to_string())'''),
]
