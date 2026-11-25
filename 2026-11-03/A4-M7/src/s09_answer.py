# ====================================================================
# Step 09 · 답변 생성 + 운영 로그 → outputs/answer_log.jsonl, outputs/answers.csv
# 질문 25개(Golden 20 + 답변 불가 5)마다:
#   검색(Metadata+BM25) → 근거 묶기 → LLM 호출 → 시간·토큰·비용·오류를 한 줄로 기록
# 실행:  python src/s09_answer.py            (OpenAI 호출, .env의 OPENAI_API_KEY 필요)
#        LLM_BACKEND=fake 이면 키 없이 흐름만 (답변·시간·토큰은 흉내낸 값)
# ====================================================================
import csv
import json
import os
import random
import re
import time

from config import BASE_DIR, DATA_DIR, OUT_DIR, OPENAI_API_KEY
from config_ops import (RETRIEVER, CHUNK_METHOD, ANSWER_K, LLM_MODEL, LLM_BACKEND,
                        MAX_RETRIES, NO_ANSWER_TEXT, PRICE)
from common import load_golden
from s05_bm25 import bm25_search

PROMPT_VERSION = "v1"
SYSTEM_PROMPT = f"""당신은 사내 영업 문서 도우미입니다.
규칙:
1. 아래 [근거]에 적힌 내용만 사용해 한국어로 짧게 답합니다.
2. 근거로 답할 수 없으면 다른 말 없이 정확히 "{NO_ANSWER_TEXT}"라고만 답합니다.
3. 문장마다 끝에 사용한 근거의 문서 ID를 [문서ID] 형식으로 붙입니다.
4. 근거의 표현 강도(예: 명시, 권장)를 바꾸지 않습니다. 근거에 없는 숫자·기간·코드를 만들지 않습니다."""


def load_questions():
    golden = [dict(g, answerable=True) for g in load_golden()]
    extra = json.load(open(DATA_DIR / "no_answer_questions.json", encoding="utf-8"))
    qs = golden + [dict(q, answerable=False, relevant_doc_ids=[], expected_keywords=[]) for q in extra]
    more = os.getenv("EXTRA_QUESTIONS")          # 미션 6: 새 유형의 질문을 더해 '질문 분포 변화' 흉내
    if more:
        qs += [dict(q, answerable=True) for q in json.load(open(BASE_DIR / more, encoding="utf-8"))]
    return qs


def retrieve(question, k=ANSWER_K):
    """Metadata+BM25 상위 k개 청크 (A4-M6 추천 조합)."""
    t = time.perf_counter()
    ranked = bm25_search(CHUNK_METHOD, question, use_filter=(RETRIEVER == "Metadata+BM25"))[:k]
    return ranked, (time.perf_counter() - t) * 1000


def build_context(chunks):
    return "\n\n".join(f"[{c['doc_id']}]\n{c['content']}" for c in chunks)


def build_messages(question, chunks):
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"[근거]\n{build_context(chunks)}\n\n[질문]\n{question}"}]


# ---------------------------------------------------------------- LLM 호출
_client = None


def _openai(messages):
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY, timeout=30)
    r = _client.chat.completions.create(model=LLM_MODEL, messages=messages, temperature=1)
    return r.choices[0].message.content.strip(), r.usage.prompt_tokens, r.usage.completion_tokens


def _fake(messages, rng):
    """키 없이 흐름을 보기 위한 흉내: 1등 근거의 첫 문장을 그대로 답으로 쓴다(답변 불가 판단은 안 함)."""
    ctx = messages[1]["content"]
    m = re.search(r"\[([A-Z0-9_]+)\]\n(.*?)(?:\n\n\[|\n\n\[질문\])", ctx, re.S)
    if not m:
        text = NO_ANSWER_TEXT
    else:
        lines = [l.strip("- ").strip() for l in m.group(2).splitlines() if l and not l.startswith("#")]
        text = f"{lines[0]} [{m.group(1)}]" if lines else NO_ANSWER_TEXT
    time.sleep(0)  # 실제로 기다리지는 않고 시간만 기록
    in_tok = int(sum(len(x["content"]) for x in messages) / 1.2)
    return text, in_tok, int(len(text) / 1.2)


def call_llm(messages, rng):
    """재시도 포함 호출. 반환: (답변, in_tok, out_tok, llm_ms, retries, error)"""
    retries, last_err = 0, None
    for attempt in range(MAX_RETRIES):
        t = time.perf_counter()
        try:
            if LLM_BACKEND == "fake":
                if rng.random() < 0.08 and attempt == 0:          # 흉내: 가끔 첫 시도 Timeout
                    raise TimeoutError("fake timeout")
                if rng.random() < 0.02:                           # 흉내: 드물게 계속 실패
                    raise ConnectionError("fake api down")
                ans, i, o = _fake(messages, rng)
                ms = rng.lognormvariate(6.9, 0.35) + i * 0.4      # 흉내낸 생성 시간(ms), 가끔 긴 꼬리
            else:
                ans, i, o = _openai(messages)
                ms = (time.perf_counter() - t) * 1000
            return ans, i, o, ms, retries, None
        except Exception as e:  # Timeout·Rate limit·서버 오류 → 잠시 쉬고 재시도
            last_err = f"{type(e).__name__}: {e}"[:120]
            retries += 1
            if LLM_BACKEND != "fake":
                time.sleep(2 ** attempt)                          # 1초, 2초, 4초 (exponential backoff)
    return "", 0, 0, 0.0, retries, last_err


def cost_usd(in_tok, out_tok):
    p = PRICE.get(LLM_MODEL, {"input": 0, "output": 0})
    return (in_tok * p["input"] + out_tok * p["output"]) / 1_000_000


def run(tag="run"):
    rng = random.Random(7)
    logs = []
    for q in load_questions():
        t0 = time.perf_counter()
        chunks, retr_ms = retrieve(q["question"])
        t1 = time.perf_counter()
        messages = build_messages(q["question"], chunks)
        prompt_ms = (time.perf_counter() - t1) * 1000
        ans, i, o, llm_ms, retries, err = call_llm(messages, rng)
        e2e = retr_ms + prompt_ms + llm_ms if LLM_BACKEND == "fake" else (time.perf_counter() - t0) * 1000
        logs.append({
            "run": tag, "backend": LLM_BACKEND, "model": LLM_MODEL, "prompt_version": PROMPT_VERSION,
            "retriever": RETRIEVER, "chunk_method": CHUNK_METHOD, "k": ANSWER_K,
            "query_id": q["query_id"], "query_type": q["query_type"], "answerable": q["answerable"],
            "question": q["question"], "relevant_doc_ids": q["relevant_doc_ids"],
            "expected_keywords": q["expected_keywords"],
            "context_doc_ids": [c["doc_id"] for c in chunks],
            "context_chunk_ids": [c["chunk_id"] for c in chunks],
            "top_score": round(chunks[0]["score"], 3) if chunks else 0.0,
            "context": build_context(chunks), "context_chars": sum(len(c["content"]) for c in chunks),
            "answer": ans, "input_tokens": i, "output_tokens": o, "cost_usd": cost_usd(i, o),
            "retrieval_ms": round(retr_ms, 2), "prompt_ms": round(prompt_ms, 2),
            "llm_ms": round(llm_ms, 1), "e2e_ms": round(e2e, 1),
            "retries": retries, "error": err,
        })
        mark = "ERR" if err else ("…" if ans == NO_ANSWER_TEXT else "OK")
        print(f"{q['query_id']} {mark:3} {llm_ms:7.0f}ms  in {i:4} out {o:3}  {ans[:50]}")
    with open(OUT_DIR / "answer_log.jsonl", "w", encoding="utf-8") as f:
        for r in logs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cols = ["query_id", "query_type", "answerable", "context_doc_ids", "answer",
            "input_tokens", "output_tokens", "llm_ms", "e2e_ms", "retries", "error"]
    with open(OUT_DIR / "answers.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(logs)
    print(f"\n저장: {len(logs)}건 → outputs/answer_log.jsonl, answers.csv  (backend={LLM_BACKEND}, K={ANSWER_K})")
    return logs


if __name__ == "__main__":
    run()
