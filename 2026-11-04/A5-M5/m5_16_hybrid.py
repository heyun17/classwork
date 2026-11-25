"""실습 16 · Vector + Graph 결합 (Reciprocal Rank Fusion)
사용 예) python m5_16_hybrid.py --embed          # 처음 한 번: 평가 질문 30개 중 캐시에 없는 것만 임베딩 (API)
        python m5_16_hybrid.py                  # 설계 질문 7개: 벡터 · 그래프 · 결합 상위 5
        python m5_16_hybrid.py --detail Q-001   # 한 질문의 세 순위표와 합친 점수
"""
import argparse

from m5lib import graph_rank, load_questions, question_vectors, recall, rrf, vector_rank

ap = argparse.ArgumentParser()
ap.add_argument("--embed", action="store_true")
ap.add_argument("--detail")
ap.add_argument("-n", type=int, default=5)
a = ap.parse_args()
QS = load_questions()
QV, st = question_vectors(QS, apply=a.embed)
if a.embed:
    print(f"평가 질문 {st['total']}개 · 캐시 적중 {st['hit']}개 · 새로 임베딩 {len(st['miss'])}개 · 토큰 {st['tokens']}\n")
N = a.n

if a.detail:
    i, q = next((i, q) for i, q in enumerate(QS) if q["id"] == a.detail)
    v, vs = vector_rank(QV[i])
    g, gi = graph_rank(q["question"])
    h, hs = rrf(v, g)
    exp = set(q["expected"])
    m = lambda d: "정답" if d in exp else "    "
    print(f"{q['id']} {q['question']}\n찾아야 할 정책 {q['expected']}\n")
    print(f"{'순위':<4}{'벡터 (가장 가까운 조각 점수)':<34}{'그래프 (출발점 → 1홉 · 2홉)':<34}{'결합 (RRF 점수)'}")
    for r in range(max(N, 7)):
        cv = f"{m(v[r])} {v[r]:<12}{vs[v[r]][0]:.2f}" if r < len(v) else ""
        cg = (f"{m(g[r])} {g[r]:<12}" + (f"1홉 {gi['score'][g[r]]}" if g[r] in gi["score"] else "2홉")) if r < len(g) else ""
        ch = f"{m(h[r])} {h[r]:<12}{hs[h[r]]:.4f}" if r < len(h) else ""
        print(f"{r + 1:<4}{cv:<34}{cg:<34}{ch}")
    print(f"\n그래프 출발점: {', '.join(gi['starts'])}" + (f" · 그래프에 없는 개념: {', '.join(gi['missing'])}" if gi["missing"] else ""))
    print(f"상위 {N} 정답 · 벡터 {recall(exp, v[:N])}/{len(exp)} · 그래프 {recall(exp, g[:N])}/{len(exp)} · 결합 {recall(exp, h[:N])}/{len(exp)}")
    raise SystemExit

DESIGN = ["Q-017", "Q-009", "Q-013", "Q-002", "Q-028", "Q-001", "Q-030"]
print(f"설계 질문 7개 · 상위 {N}개 정책\n")
print(f"{'질문':<7}{'정답 수':>5}{'벡터':>8}{'그래프':>8}{'결합':>8}")
S = [0, 0, 0, 0]
for i, q in enumerate(QS):
    if q["id"] not in DESIGN:
        continue
    v, _ = vector_rank(QV[i])
    g, _ = graph_rank(q["question"])
    h, _ = rrf(v, g)
    r = [recall(q["expected"], x[:N]) for x in (v, g, h)]
    e = len(q["expected"])
    S = [S[0] + e] + [S[k + 1] + r[k] for k in range(3)]
    print(f"{q['id']:<7}{e:>5}" + "".join(f"{f'{x}/{e}':>8}" for x in r))
print(f"{'합계':<7}{S[0]:>5}" + "".join(f"{f'{x}/{S[0]}':>8}" for x in S[1:]))
