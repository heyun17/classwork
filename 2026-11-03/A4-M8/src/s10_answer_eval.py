# ====================================================================
# Step 10 · 답변 품질 평가 → outputs/answer_eval.csv, answer_quality_summary.csv
# 규칙 기반(Rule-based) 채점: 키 없이 항상 동작
#   근거성(grounded_rule)  답변의 숫자·기간·제품코드가 모두 근거 안에 있나
#   인용 유효(citation_valid)  인용한 [문서ID]가 실제로 넘겨준 근거에 있나
#   인용 정확(citation_acc)    인용한 문서가 정답 문서인가
#   인용 커버리지(citation_cov) 문장 중 인용이 붙은 비율
#   완전성(keyword_cov)     기대 키워드가 답변에 나온 비율
#   답변 보류(abstained)     "확인할 수 없습니다"라고 했나 → 답변 불가 질문에서 맞게 보류했나
# 선택: USE_JUDGE=1 이면 LLM-as-a-Judge로 Groundedness·Faithfulness·Relevance(1~5)를 추가
# 실행:  python src/s10_answer_eval.py              (s09 결과 채점)
#        python src/s10_answer_eval.py --samples    (data/answer_samples.json 손답변 채점 — 키 불필요)
# ====================================================================
import csv
import json
import os
import re
import sys
from collections import defaultdict

from config import DATA_DIR, OUT_DIR, OPENAI_API_KEY
from config_ops import NO_ANSWER_TEXT, JUDGE_MODEL

CODE_RE = re.compile(r"[A-Z]{2,}-[A-Z]+-\d{2}")
NUM_RE = re.compile(r"\d+(?:\.\d+)?\s?(?:년|개월|일|%|원|만원|시간|대|개)")
CITE_RE = re.compile(r"\[([A-Z0-9_]+)\]")


def norm(t):
    return re.sub(r"\s+", "", t)


def facts(text):
    """답변에서 '근거에 있어야 하는 사실'을 뽑는다: 제품코드, 숫자+단위."""
    body = CITE_RE.sub("", text)
    return set(CODE_RE.findall(body)) | {norm(n) for n in NUM_RE.findall(body)}


def supported(fact, ctx):
    """사실이 근거에 있나. 숫자 앞에 다른 숫자가 붙은 경우(2025년 안의 '5년')는 인정하지 않는다.
    연도(2026년)는 근거에 '2026'만 있어도 인정한다."""
    c = norm(ctx)
    if re.fullmatch(r"\d{4}년", fact):
        fact = fact[:-1]
    return re.search(r"(?<![0-9])" + re.escape(fact), c) is not None


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?다요])\s+|\n+", text.strip()) if len(norm(CITE_RE.sub("", s))) > 3]


def score_rule(r):
    ans, ctx = r["answer"], r["context"]
    abst = NO_ANSWER_TEXT.rstrip(".") in ans or "확인할 수 없" in ans
    cited = CITE_RE.findall(ans)
    ctx_ids, rel = set(r["context_doc_ids"]), set(r["relevant_doc_ids"])
    unsupported = sorted(f for f in facts(ans) if not supported(f, ctx))
    sents = sentences(ans)
    kw = r["expected_keywords"]
    out = {
        "abstained": abst,
        "retrieval_hit": bool(rel & ctx_ids) if r["answerable"] else None,
        "grounded_rule": None if abst or r["error"] else int(not unsupported),
        "unsupported": " ".join(unsupported),
        "citation_valid": None if abst or not cited else round(sum(c in ctx_ids for c in cited) / len(cited), 3),
        "citation_acc": None if abst or not cited or not r["answerable"] else round(sum(c in rel for c in cited) / len(cited), 3),
        "citation_cov": None if abst or not sents else round(sum(bool(CITE_RE.search(s)) for s in sents) / len(sents), 3),
        "keyword_cov": None if not kw or abst else round(sum(norm(k) in norm(ans) for k in kw) / len(kw), 3),
    }
    if r["error"]:
        verdict = "ERROR"
    elif not r["answerable"]:
        verdict = "PASS" if abst else "FAIL·근거없는답변"
    elif abst:
        verdict = "FAIL·과도한보류"
    elif unsupported:
        verdict = "FAIL·근거없는사실"
    elif out["citation_valid"] is None:
        verdict = "FAIL·출처없음"
    elif out["citation_valid"] < 1:
        verdict = "FAIL·없는출처"
    elif out["citation_acc"] == 0:
        verdict = "FAIL·엉뚱한출처"
    elif out["keyword_cov"] is not None and out["keyword_cov"] < 0.6:
        verdict = "WARN·불완전"
    else:
        verdict = "PASS"
    out["verdict"] = verdict
    # 검색 × 답변 4분면 (답변 가능한 질문만)
    if r["answerable"] and not r["error"]:
        good_ans = verdict == "PASS"
        out["quadrant"] = {(True, True): "①검색O·답변O", (True, False): "②검색O·답변X",
                           (False, True): "③검색X·답변O(위험)", (False, False): "④검색X·답변X"}[(out["retrieval_hit"], good_ans)]
    else:
        out["quadrant"] = ""
    return out


JUDGE_PROMPT = """너는 RAG 답변 평가자다. [근거]와 [질문], [답변]을 보고 1~5점으로 채점한다.
- groundedness: 답변의 모든 주장이 근거로 뒷받침되는가 (근거에 없는 사실이 있으면 낮게)
- faithfulness: 근거의 의미·강도·조건을 바꾸지 않았는가 (권장→필수 같은 과장이 있으면 낮게)
- relevance: 질문에 실제로 답했는가
반드시 JSON 한 줄로만: {"groundedness": n, "faithfulness": n, "relevance": n, "reason": "한 문장"}"""


def judge(r):
    from openai import OpenAI
    c = OpenAI(api_key=OPENAI_API_KEY)
    msg = f"[근거]\n{r['context']}\n\n[질문]\n{r['question']}\n\n[답변]\n{r['answer']}"
    res = c.chat.completions.create(model=JUDGE_MODEL, temperature=0,
                                    messages=[{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": msg}])
    txt = res.choices[0].message.content
    try:
        return json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    except ValueError:
        return {"reason": "judge 응답 파싱 실패: " + txt[:60]}


def load_rows(samples=False):
    if not samples:
        return [json.loads(l) for l in open(OUT_DIR / "answer_log.jsonl", encoding="utf-8")]
    from s09_answer import load_questions, retrieve, build_context
    qs = {q["query_id"]: q for q in load_questions()}
    rows = []
    for s in json.load(open(DATA_DIR / "answer_samples.json", encoding="utf-8")):
        q = qs[s["query_id"]]
        chunks, _ = retrieve(q["question"])
        rows.append(dict(q, sample_id=s["sample_id"], label=s["label"], answer=s["answer"], error=None,
                         context_doc_ids=[c["doc_id"] for c in chunks], context=build_context(chunks)))
    return rows


def avg(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def summarize(ev):
    ans = [e for e in ev if e["answerable"] and not e["error"]]
    na = [e for e in ev if not e["answerable"] and not e["error"]]
    return {
        "n": len(ev), "answerable": len(ans), "no_answer": len(na),
        "pass_rate": avg([e["verdict"] == "PASS" for e in ev]),
        "retrieval_hit": avg([e["retrieval_hit"] for e in ans]),
        "grounded_rule": avg([e["grounded_rule"] for e in ans]),
        "citation_valid": avg([e["citation_valid"] for e in ans]),
        "citation_acc": avg([e["citation_acc"] for e in ans]),
        "citation_cov": avg([e["citation_cov"] for e in ans]),
        "keyword_cov": avg([e["keyword_cov"] for e in ans]),
        "abstention_accuracy": avg([e["abstained"] for e in na]),
        "over_abstention": avg([e["abstained"] for e in ans]),
    }


if __name__ == "__main__":
    samples = "--samples" in sys.argv
    rows = load_rows(samples)
    use_judge = os.getenv("USE_JUDGE") == "1" and OPENAI_API_KEY
    ev = []
    for r in rows:
        e = {k: r.get(k) for k in ["sample_id", "label", "query_id", "query_type", "answerable", "question", "answer", "error"]}
        e.update(score_rule(r))
        if use_judge and not r["error"]:
            j = judge(r)
            e.update({f"judge_{k}": v for k, v in j.items()})
        ev.append(e)
    name = "answer_eval_samples.csv" if samples else "answer_eval.csv"
    keys = list(dict.fromkeys(k for e in ev for k in e))
    with open(OUT_DIR / name, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(ev)
    if samples:
        print(f"{'샘플':4} {'의도':22} {'판정':16} 근거성 인용유효 인용정확 키워드  근거에없는것")
        for e in ev:
            print(f"{e['sample_id']:4} {e['label']:22} {e['verdict']:16} {str(e['grounded_rule']):5} "
                  f"{str(e['citation_valid']):7} {str(e['citation_acc']):7} {str(e['keyword_cov']):6} {e['unsupported']}")
    else:
        s = summarize(ev)
        with open(OUT_DIR / "answer_quality_summary.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=s.keys()); w.writeheader(); w.writerow(s)
        for k, v in s.items():
            print(f"{k:22} {v}")
        quad = defaultdict(int)
        for e in ev:
            if e["quadrant"]:
                quad[e["quadrant"]] += 1
        print("\n검색×답변 4분면:", dict(sorted(quad.items())))
        print("판정:", dict(sorted(defaultdict(int, {v: sum(e['verdict'] == v for e in ev) for v in {e['verdict'] for e in ev}}).items())))
    print("저장 →", f"outputs/{name}")
