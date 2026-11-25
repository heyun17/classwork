"""A5-M6 공통 — 검색(auto) + 검색 실패 판정 + 답변 생성 · 검증."""
import json

from m3lib import ROOT
from m5lib import load_questions, question_vectors, vector_rank
from m5_retriever import Retriever

T = json.loads((ROOT / "design" / "m6_tests.json").read_text(encoding="utf-8"))
MIN_SCORE = T["min_score"]


def tests():
    return T["tests"]


def eval_as_tests(ids):
    """평가 질문을 테스트 모양으로 (answerability → 기대 상태)"""
    import csv
    m = {"answerable": ["answered", "conditional"], "conditional": ["conditional", "answered"], "unanswerable": ["refused", "insufficient"]}
    rows = {r["question_id"]: r for r in csv.DictReader(open(ROOT / "reference" / "evaluation_questions_30.csv", encoding="utf-8-sig"))}
    return [{"id": i, "kind": rows[i]["scenario_type"], "question": rows[i]["question"], "expect_docs": rows[i]["expected_doc_ids"].split("|"),
             "expect_status": m.get(rows[i]["answerability"], ["answered"]), "expected_answer": rows[i]["expected_answer"]} for i in ids]


def retrieve(items, apply=False):
    """질문들 → 검색 결과 + 가장 가까운 정책 점수 + 검색 실패 여부"""
    qv, st = question_vectors(items, apply=apply)
    R = Retriever("auto", 5)
    out = []
    for i, t in enumerate(items):
        res = R.search(t["question"], qv[i])
        order, best = vector_rank(qv[i])
        res["top_score"] = round(best[order[0]][0], 3)
        res["no_evidence"] = res["top_score"] < MIN_SCORE and not res["rules_fired"]
        out.append(res)
    return out, st
