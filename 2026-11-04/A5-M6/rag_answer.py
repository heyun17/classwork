"""답변 생성 + 인용 검증 (M6의 미리보기). 검색기 결과(근거 패키지)만 보고 답하게 한다."""
import hashlib
import re

from m2lib import ask_json

SYSTEM = ("너는 쇼핑몰 고객센터 상담원을 돕는다. 아래 [근거]에 있는 내용만으로 답한다. 근거에 없으면 모른다고 답한다. "
          "주문 날짜가 있으면 그 날짜에 유효한 정책 버전을 쓴다. 반드시 JSON 하나로만 답한다.")


def build_context(res, per_doc=2, max_docs=4):
    rows = []
    for r in res["results"][:max_docs]:
        for e in r["evidence"][:per_doc]:
            rows.append({"chunk_id": e["chunk_id"], "doc_id": r["doc_id"], "title": r["title"], "text": e["text"]})
    return rows


def prompt(question, ctx, flags):
    ev = "\n\n".join(f"[{c['chunk_id']}] ({c['title']})\n{c['text']}" for c in ctx)
    rule = ""
    if "restricted" in flags:
        rule = "\n- 이 질문은 내부 정보나 개인 정보를 묻는다. 공개 정책에 근거가 없으면 정보를 제공하지 않는다고 답한다 (status=refused)."
    return f"""질문: {question}

[근거]
{ev}

[규칙]
- 답은 2~4문장. 근거에 없는 숫자나 조건을 만들지 않는다.
- citations에는 실제로 쓴 근거의 chunk_id와, 그 근거에서 그대로 옮긴 짧은 문장(quote)을 넣는다.
- status: answered(근거로 답함) · conditional(조건에 따라 다름) · insufficient(근거 부족) · refused(답하면 안 됨){rule}

JSON 형식:
{{"answer": "", "status": "", "citations": [{{"chunk_id": "", "quote": ""}}]}}"""


def squash(s):
    return re.sub(r"\s+", "", s or "")


def verify(answer, ctx, question=None):
    """인용 검증: (1) 인용한 조각이 근거에 있나 (2) quote가 그 조각 원문에 그대로 있나 (3) 답의 숫자가 인용 근거에 있나
    question을 주면, 질문에 이미 있던 숫자(고객이 말한 날짜 · 금액 · 시간)는 근거에서 찾지 않는다."""
    by = {c["chunk_id"]: c for c in ctx}
    checks = []
    for c in answer.get("citations", []):
        cid = c.get("chunk_id")
        in_ctx = cid in by
        quoted = in_ctx and squash(c.get("quote")) in squash(by[cid]["text"])
        checks.append({"chunk_id": cid, "in_context": in_ctx, "quote_found": bool(quoted)})
    cited = " ".join(by[c["chunk_id"]]["text"] for c in checks if c["in_context"])
    nums = re.findall(r"\d[\d,~.]*\s*(?:영업일|시간|일|원|%)", answer.get("answer", ""))
    asked = squash(question or "")
    num_checks = [{"value": n, "found": squash(n) in squash(cited), "in_question": bool(question) and squash(n) in asked} for n in nums]
    ok = all(x["in_context"] and x["quote_found"] for x in checks) and all(n["found"] or n["in_question"] for n in num_checks)
    return {"ok": ok, "citations": checks, "numbers": num_checks}


def rule_sections(res, section="업무 규정"):
    """규칙으로 고정(pin)된 정책은 '업무 규정' 조각을 근거에 꼭 넣는다 — 버전별 숫자가 그 소제목에 있기 때문"""
    from m5lib import CHUNKS
    pinned = [r["doc_id"] for r in res["results"] if r["rules"]]
    rows = []
    for d in pinned:
        for cid, c in CHUNKS.items():
            if c["doc_id"] == d and c.get("section") == section:
                rows.append({"chunk_id": cid, "doc_id": d, "title": c.get("title", d), "text": c["text"]})
    return rows


def answer(question, res, dry_run=False, refresh=False, extra_ctx=None):
    ctx = build_context(res)
    for e in extra_ctx or []:
        if e["chunk_id"] not in {c["chunk_id"] for c in ctx}:
            ctx.append(e)
    p = prompt(question, ctx, res.get("flags", []))
    key = question + res["route"] + "|".join(r["doc_id"] for r in res["results"])
    if extra_ctx:
        key += "|ctx:" + "|".join(c["chunk_id"] for c in ctx)
    name = "answer_" + hashlib.sha256(key.encode()).hexdigest()[:12]
    rec = ask_json(name, SYSTEM, p, dry_run=dry_run, refresh=refresh)
    if rec is None:
        return None, ctx, p
    return rec, ctx, p
