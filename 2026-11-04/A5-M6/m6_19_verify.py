"""실습 19 · 원문 근거 검증 (API 호출 없음)
① 검색기가 돌려준 근거 조각이 정말 원문(dataset/md · faq.csv)에 그대로 있나 — 평가 질문 30개
② 답변 검증기(rag_answer.verify)가 잘못된 답을 잡아내나 — 일부러 만든 답 5개
사용 예) python m6_19_verify.py
"""
import re

from m1lib import load_faq, load_policies
from m5lib import load_questions, question_vectors
from m5_retriever import Retriever
from rag_answer import build_context, verify

SRC = {d["id"]: re.sub(r"\s+", "", d["text"]) for d in load_policies() + load_faq()}

print("[1] 검색 결과의 근거 조각 → 원문 대조 (평가 질문 30개, auto, 상위 5 정책 × 조각 2)")
QS = load_questions()
QV, _ = question_vectors(QS)
R = Retriever("auto", 5)
n = ok = 0
bad = []
for i, q in enumerate(QS):
    res = R.search(q["question"], QV[i])
    for r in res["results"]:
        for e in r["evidence"]:
            body = e["text"].split("\n", 1)[-1]  # 첫 줄 '제목 > 소제목'은 청킹 때 붙인 머리말
            n += 1
            if re.sub(r"\s+", "", body)[:200] in SRC[r["doc_id"]]:
                ok += 1
            else:
                bad.append((q["id"], e["chunk_id"]))
    for r in res["results"]:
        for p in r["path"]:
            n += 1
            if re.sub(r"\s+", "", p["evidence"]) in SRC[p["doc_id"]]:
                ok += 1
            else:
                bad.append((q["id"], "경로 " + p["edge"]))
print(f"    근거 조각 + 그래프 경로 근거 {n}개 중 원문과 일치 {ok}개" + (f" · 불일치 {bad[:5]}" if bad else ""))

print("\n[2] 답변 검증기 시험 — Q-005(9월 25일 주문 카드 환불) 근거로 일부러 만든 답 5개")
i = [q["id"] for q in QS].index("Q-005")
res = R.search(QS[i]["question"], QV[i])
ctx = build_context(res)
print("    넘겨준 근거 조각: " + ", ".join(c["chunk_id"] for c in ctx))
cases = [
    ("근거대로 쓴 답", {"answer": "9월 주문은 주문일 기준 v1 정책을 쓰고, 환불 기간은 환불 승인일부터 셉니다.",
                      "citations": [{"chunk_id": "EXC-007#6", "quote": "환불 처리 기간의 시작은 주문일이 아니라 환불 승인일이다"}]}),
    ("인용 문장을 바꿔 쓴 답", {"answer": "환불 기간은 주문일부터 셉니다.",
                        "citations": [{"chunk_id": "EXC-007#6", "quote": "환불 기간은 주문일부터 센다"}]}),
    ("근거에 없는 숫자", {"answer": "9월 주문의 카드 환불은 승인 후 5~7영업일입니다.",
                     "citations": [{"chunk_id": "EXC-007#1", "quote": "카드 환불 기간, VIP 무료배송 기준"}]}),
    ("넘겨주지 않은 조각 인용", {"answer": "v1 카드 환불은 승인 후 5~7영업일입니다.",
                         "citations": [{"chunk_id": "EXC-007#2", "quote": "v1은 카드 환불 승인 후 5~7영업일"}]}),
    ("버전이 틀린 답 (9월 주문에 10월 기준)", {"answer": "카드 환불은 승인 후 3~5영업일입니다.",
                                      "citations": [{"chunk_id": "POL-REF-001#2", "quote": "환불 승인 이후 카드 결제 3~5영업일"}]}),
]
for name, a in cases:
    v = verify(a, ctx)
    why = []
    for c in v["citations"]:
        if not c["in_context"]:
            why.append(f"{c['chunk_id']} 근거 밖")
        elif not c["quote_found"]:
            why.append(f"{c['chunk_id']} 인용 불일치")
    for x in v["numbers"]:
        if not x["found"]:
            why.append(f"숫자 {x['value']} 근거에 없음")
    print(f"    {'통과' if v['ok'] else '걸림'}  {name:<22} {' · '.join(why) or '-'}")
print("\n    → 마지막 답은 인용 · 숫자가 모두 근거와 맞아 통과하지만, 9월 주문의 정답(v1 5~7영업일)이 아니다.")
print("      인용 검증은 '근거에 있는 말인가'만 본다. '맞는 근거를 골랐나'는 검색과 테스트(실습 20 · 21)가 본다.")
