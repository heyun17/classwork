"""실습 15 · 온톨로지 관계로 넓히는 동적 필터
① 조각 상위 5        : 벡터로 찾은 조각 5개의 문서
② 정책 상위 N        : 정책마다 가장 가까운 조각 점수로 정책 순위를 매겨 N개 (같은 문서가 여러 칸을 차지하지 않게)
③ 제한 필터          : ②에 메타데이터 조건 / 온톨로지 그래프로 후보를 '줄이는' 필터를 건 것
④ 확장 동적 필터     : ② 상위 정책 + 그 정책과 '함께적용'으로 이어진 정책을 후보로 넓히고, 그 안에서 벡터 점수로 N개
사용 예) python m4_15_dynamic.py
        python m4_15_dynamic.py --detail Q-001
        python m4_15_dynamic.py --seed 5 --keep 7
"""
import argparse

from m3lib import hop_search, load_graph, start_nodes
from m4lib import build_embeddings, hit, load_chunks, match, questions, unit

ap = argparse.ArgumentParser()
ap.add_argument("--detail")
ap.add_argument("--seed", type=int, default=5, help="확장의 출발이 되는 상위 정책 수")
ap.add_argument("--keep", type=int, default=7, help="최종으로 남길 정책 수")
a = ap.parse_args()
E = build_embeddings()
X, Q, ids = unit(E["chunk_vecs"]), unit(E["q_vecs"]), E["chunk_ids"]
chunks = {c["chunk_id"]: c for c in load_chunks()}
G = load_graph()
QS = questions()


def policy_scores(i, cond=None):
    """정책마다 가장 가까운 조각의 점수 (cond가 있으면 조건에 맞는 조각만)"""
    s = X @ Q[i]
    best = {}
    for j, v in enumerate(s):
        c = chunks[ids[j]]
        if c["kind"] == "policy" and (cond is None or match(c["meta"], cond)):
            if float(v) > best.get(c["doc_id"], (-1, ""))[0]:
                best[c["doc_id"]] = (float(v), ids[j])
    return best


def together(p):
    """온톨로지 그래프에서 p와 '함께적용'으로 이어진 정책 (방향 무관)"""
    out = set()
    for s, o, k in list(G.out_edges(p, keys=True)) + list(G.in_edges(p, keys=True)):
        if k == "함께적용":
            out.add(o if s == p else s)
    return out


def top(scores, n, allow=None):
    keys = [d for d in scores if allow is None or d in allow]
    return sorted(keys, key=lambda d: -scores[d][0])[:n]


def expand(i):
    sc = policy_scores(i)
    seed = top(sc, a.seed)
    added = {x: d for d in seed for x in together(d) if x not in seed}
    cand = set(seed) | set(added)
    return sc, seed, added, top(sc, a.keep, cand)


def methods(i, q):
    sc = policy_scores(i)
    first5 = []
    for j in (X @ Q[i]).argsort()[::-1][:5]:
        d = chunks[ids[j]]["doc_id"]
        if d not in first5:
            first5.append(d)
    starts, _ = start_nodes(G, q["question"])
    h1, h2, _, _ = hop_search(G, starts)
    onto = set(h1) | set(h2)
    meta = policy_scores(i, q["conditions"])
    return {"① 조각 상위 5": first5,
            f"② 정책 상위 {a.keep}": top(sc, a.keep),
            f"③ 메타 제한 {a.keep}": top(meta, a.keep),
            f"③ 온톨 제한 {a.keep}": top(sc, a.keep, onto),
            f"④ 확장 동적 {a.keep}": expand(i)[3]}


if a.detail:
    i, q = next((i, q) for i, q in enumerate(QS) if q["id"] == a.detail)
    sc, seed, added, final = expand(i)
    exp = set(q["expected"])
    mark = lambda d: "정답" if d in exp else "    "
    print(f"{q['id']} {q['question']}\n찾아야 할 정책 {q['expected']}\n")
    print(f"[1] 벡터로 정한 상위 정책 {a.seed}개 (정책마다 가장 가까운 조각 점수)")
    for d in seed:
        print(f"   {mark(d)} {d:<12} {sc[d][0]:.2f}  {sc[d][1]}")
    print("[2] 온톨로지 '함께적용'으로 더한 정책")
    for d, src in added.items():
        print(f"   {mark(d)} {d:<12} {sc[d][0]:.2f}  ← {src}")
    print(f"[3] 넓힌 후보 {len(seed) + len(added)}개 안에서 벡터 점수 상위 {a.keep}개")
    for d in final:
        print(f"   {mark(d)} {d:<12} {sc[d][0]:.2f}")
    print(f"\n정답 {len(exp & set(final))}/{len(exp)} · 빠진 정책 {sorted(exp - set(final)) or '없음'}")
    print(f"비교: 확장 없이 정책 상위 {a.keep}개 → 정답 {len(exp & set(top(sc, a.keep)))}/{len(exp)}")
    raise SystemExit

names = list(methods(0, QS[0]))
tot = sum(len(q["expected"]) for q in QS)
S = {n: [0, 0] for n in names}
print(f"{'질문':<7}" + "".join(f"{n:>14}" for n in names))
for i, q in enumerate(QS):
    m = methods(i, q)
    e = len(q["expected"])
    cells = []
    for n in names:
        h = hit(q["expected"], m[n])
        S[n][0] += h
        S[n][1] += len(m[n])
        cells.append(f"{h}/{e}")
    print(f"{q['id']:<7}" + "".join(f"{c:>14}" for c in cells))
print(f"{'정답 합계':<7}" + "".join(f"{f'{S[n][0]}/{tot}':>14}" for n in names))
print(f"{'정책 수':<7}" + "".join(f"{S[n][1]:>14}" for n in names))
print(f"\n확장 동적 필터: 상위 정책 {a.seed}개 + 함께적용 이웃 → 그 안에서 {a.keep}개")
