# ====================================================================
# A4-M8 · Document Update Agent 실행기
#   Trigger: 사람이 실행 (python src/agent_run.py) — 실무에서는 파일 감시·일정·이벤트가 부름
#   AGENT_BACKEND=openai : LLM(gpt-6-luna)이 Tool을 골라 가며 진행 (Agent)
#   AGENT_BACKEND=rule   : 정해진 순서대로 진행 (Workflow) — 키 없이 동작, 비교용
#   APPROVAL=ask(기본)/yes/no : 사람 승인 방식. ask면 터미널에서 y/n 입력
# 결과: agent_state/state.json(Memory), trace.jsonl(행동 기록), report.md(보고서)
# ====================================================================
import json
import os
import sys

from config import OPENAI_API_KEY
import agent_tools as T

BACKEND = os.getenv("AGENT_BACKEND", "openai")
APPROVAL = os.getenv("APPROVAL", "ask")
MODEL = os.getenv("AGENT_MODEL", "gpt-6-luna")
MAX_STEPS = 40

SYSTEM = """너는 사내 RAG 문서 저장소를 관리하는 Document Update Agent다.
목표: inbox/의 새 파일을 검사해 안전한 것만 RAG에 반영하고, 나머지는 보류·거부한 뒤 보고서를 쓴다.
절차(파일마다): read_file → (형식 문제면 reject_file) → propose_metadata → validate_metadata
  → (errors 있으면 hold_file) → stage_and_evaluate
  → needs_approval 또는 regression이 있으면 request_approval → 승인 yes면 commit_document, 아니면 hold_file
  → 둘 다 없으면 commit_document
규칙:
- 이미 committed/rejected이고 내용이 같은(memory.same_content=true) 파일은 다시 처리하지 않는다.
- commit 전에 반드시 stage_and_evaluate를 한다. 메타데이터를 임의로 지어내지 않는다.
- 기존 문서 삭제·대량 변경은 하지 않는다.
- 모든 파일을 처리한 뒤 write_report를 한 번 호출하고 끝낸다. 보고서 요약은 한국어 3문장 이내."""


def approver(file, reason):
    if APPROVAL in ("yes", "no"):
        print(f"    🙋 승인 요청 [{file}] {reason}  → 자동 {APPROVAL}")
        return APPROVAL
    if not sys.stdin.isatty():
        return "no"
    a = input(f"    🙋 승인 요청 [{file}]\n       사유: {reason}\n       승인할까요? (y/n) ").strip().lower()
    return "yes" if a in ("y", "yes", "예", "ㅇ") else "no"


TOOLS = {
    "list_inbox": lambda a: T.list_inbox(),
    "read_file": lambda a: T.read_file(a["file"]),
    "propose_metadata": lambda a: T.propose_metadata(a["file"]),
    "validate_metadata": lambda a: T.validate_metadata(a["file"], a["metadata"]),
    "stage_and_evaluate": lambda a: T.stage_and_evaluate(a["file"], a["metadata"]),
    "request_approval": lambda a: T.request_approval(a["file"], a["reason"], approver),
    "commit_document": lambda a: T.commit_document(a["file"], a["metadata"]),
    "hold_file": lambda a: T.hold_file(a["file"], a["reason"]),
    "reject_file": lambda a: T.reject_file(a["file"], a["reason"]),
    "write_report": lambda a: T.write_report(a["summary"]),
}


def call(step, name, args):
    try:
        res = TOOLS[name](args)
    except Exception as e:  # Tool 오류도 결과로 돌려줘 LLM이 다음 행동을 고르게 함
        res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    T.trace(step, name, args, res)
    short = json.dumps(res, ensure_ascii=False)
    print(f"[{step:02d}] {name}({', '.join(f'{k}={str(v)[:28]}' for k, v in args.items() if k != 'metadata')})"
          f" → {short[:150]}{'…' if len(short) > 150 else ''}")
    return res


# ------------------------------------------------------------ Workflow (규칙 순서)
def run_rule():
    step = 0
    def c(name, **a):
        nonlocal step
        step += 1
        return call(step, name, a)
    for f in c("list_inbox")["files"]:
        mem = f["memory"]
        if mem and mem["same_content"] and mem["status"] in ("committed", "rejected"):
            print(f"     ↳ {f['file']}: 이미 처리됨({mem['status']}) — 건너뜀")
            continue
        name = f["file"]
        r = c("read_file", file=name)
        if not r["ok"]:
            c("reject_file", file=name, reason="; ".join(r["problems"])); continue
        meta = c("propose_metadata", file=name)
        meta.pop("all_codes_in_text", None)
        v = c("validate_metadata", file=name, metadata=meta)
        if not v["ok"]:
            c("hold_file", file=name, reason="; ".join(v["errors"])); continue
        ev = c("stage_and_evaluate", file=name, metadata=meta)
        need = v["needs_approval"] + ev["regression_reasons"]
        if need:
            ap = c("request_approval", file=name, reason=" / ".join(need))
            if not ap["approved"]:
                c("hold_file", file=name, reason="승인 거절: " + " / ".join(need)); continue
        c("commit_document", file=name, metadata=meta)
    c("write_report", summary="규칙 Workflow로 inbox를 처리했습니다.")


# ------------------------------------------------------------ Agent (LLM이 Tool 선택)
def run_llm():
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": "inbox를 처리해 줘. list_inbox부터 시작해."}]
    for step in range(1, MAX_STEPS + 1):
        r = client.chat.completions.create(model=MODEL, messages=messages, tools=T.TOOL_SPECS, reasoning_effort="none")
        msg = r.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            print(f"[{step:02d}] (Agent 종료) {msg.content}")
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            res = call(step, tc.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
            if tc.function.name == "write_report":
                print("보고서 → agent_state/report.md")
    print(f"⚠ MAX_STEPS({MAX_STEPS})에 도달해 멈췄습니다 — 무한 반복 방지 Guardrail")


if __name__ == "__main__":
    print(f"backend={BACKEND} approval={APPROVAL}\n")
    run_rule() if BACKEND == "rule" or not OPENAI_API_KEY else run_llm()
    st = T.load_state()
    print("\n파일별 결과:")
    for f, r in st["files"].items():
        print(f"  {r.get('status'):10} {f}  {r.get('reason', '') or '; '.join(r.get('eval', {}).get('regression', []))}")
    print("현재 버전:", st["version"], "| 마지막 평가:", st["last_eval"])
