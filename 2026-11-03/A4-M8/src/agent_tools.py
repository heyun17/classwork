# ====================================================================
# A4-M8 · Document Update Agent의 Tool 모음
#   Agent(LLM)는 '언제 어떤 Tool을 쓸지'만 판단하고, 실제 일은 여기 함수들이 한다.
#   Guardrail은 프롬프트가 아니라 이 코드 안에서 강제한다 (commit_document, rollback_last).
#
#   inbox/ 의 새 파일 → read_file → propose_metadata → validate_metadata
#   → stage_and_evaluate (Golden 회귀 평가) → commit_document / request_approval / hold_file / reject_file
# ====================================================================
import csv
import hashlib
import json
import re
import shutil
import statistics
import time
from pathlib import Path

from rank_bm25 import BM25Okapi

from config import BASE_DIR, DOCS_DIR, OUT_DIR, METADATA_CSV, META_FIELDS
from common import (load_metadata, load_golden, read_doc, tokenize, extract_filters, match_filters,
                    to_doc_ranking, recall_at_k, hit_at_k, reciprocal_rank, ndcg_at_k)

INBOX = BASE_DIR / "inbox"
STATE_DIR = BASE_DIR / "agent_state"
STATE_FILE = STATE_DIR / "state.json"
TRACE_FILE = STATE_DIR / "trace.jsonl"
STATE_DIR.mkdir(exist_ok=True)

EVAL_K = 3
# 회귀(Regression) 판정 기준 — 하나라도 넘으면 '품질 저하'
REGRESSION_RULES = {"recall_drop": 0.02, "mrr_drop": 0.02, "lost_hits": 0}

REGION_EN = {"서울": "SEOUL", "부산": "BUSAN", "광주": "GWANGJU", "대전": "DAEJEON", "인천": "INCHEON",
             "대구": "DAEGU", "울산": "ULSAN", "세종": "SEJONG", "제주": "JEJU"}
CUSTOMER_EN = {"공공기관": "PUBLIC", "기업": "CORP"}
PRODUCT_EN = {"노트북": "NOTEBOOK", "복합기": "MFP"}


# ------------------------------------------------------------ Memory / State
def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"version": 0, "files": {}, "approvals": {}, "last_eval": None, "history": []}


def save_state(s):
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def trace(step, tool, args, result):
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "step": step, "tool": tool, "args": args,
                            "result": result}, ensure_ascii=False) + "\n")


def _sha1(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


# ------------------------------------------------------------ 청킹 (s03과 같은 규칙)
def chunk_heading(text, min_chars=40):
    title = re.findall(r"^# (.+)$", text, flags=re.M)[0]
    parts = [p.strip() for p in re.split(r"\n(?=## )", text) if p.strip().startswith("## ")]
    merged, buf = [], ""
    for p in parts:
        buf = (buf + "\n\n" + p).strip() if buf else p
        if len(buf) >= min_chars:
            merged.append(buf); buf = ""
    if buf:
        if merged: merged[-1] += "\n\n" + buf
        else: merged.append(buf)
    return [f"# {title}\n{m}" for m in merged]


def build_chunks(meta_rows, override_text=None):
    """메타데이터 전체로 heading 청크 목록을 만든다. override_text={doc_id: 새 본문} 이면 그 본문을 쓴다."""
    override_text = override_text or {}
    chunks = []
    for m in meta_rows:
        text = override_text.get(m["doc_id"]) or read_doc(m["source_file"])
        for i, piece in enumerate(chunk_heading(text)):
            chunks.append({"chunk_id": f'{m["doc_id"]}__heading__{i:02d}', "doc_id": m["doc_id"],
                           "chunk_method": "heading", "chunk_order": i, "content": piece, "char_count": len(piece),
                           "source_file": m["source_file"], **{k: m[k] for k in META_FIELDS}})
    return chunks


# ------------------------------------------------------------ 평가 (A4-M6 Metadata+BM25 · heading · K=3)
def evaluate_chunks(chunks, k=EVAL_K):
    bm = BM25Okapi([tokenize(c["content"]) for c in chunks])
    per = {}
    for g in load_golden():
        scores = bm.get_scores(tokenize(g["question"]))
        flt = extract_filters(g["question"])
        ranked = sorted((dict(c, score=float(s)) for c, s in zip(chunks, scores) if match_filters(c, flt)),
                        key=lambda c: -c["score"])
        docs, _ = to_doc_ranking(ranked, 10)
        rel = g["relevant_doc_ids"]
        per[g["query_id"]] = {"top3": docs[:k], "recall": recall_at_k(docs, rel, k), "hit": hit_at_k(docs, rel, k),
                              "rr": reciprocal_rank(docs[:k], rel), "ndcg": ndcg_at_k(docs, rel, k)}
    summary = {m: round(statistics.mean(v[m] for v in per.values()), 4) for m in ["recall", "hit", "rr", "ndcg"]}
    summary["mrr"] = summary.pop("rr")
    return summary, per


# ============================================================ Tools
def list_inbox():
    """inbox/ 파일 목록과 처리 이력(Memory)을 돌려준다."""
    st = load_state()
    out = []
    for p in sorted(INBOX.glob("*")):
        if p.is_file() and not p.name.startswith("."):
            h = _sha1(p.read_text(encoding="utf-8", errors="ignore"))
            prev = st["files"].get(p.name)
            out.append({"file": p.name, "sha1": h,
                        "memory": None if not prev else {"status": prev["status"], "same_content": prev.get("sha1") == h}})
    return {"files": out}


def read_file(file):
    """파일을 읽고 형식을 검사한다: 확장자, H1 제목, H2 섹션, 길이, 기존 문서와 같은 파일명/제목인지."""
    p = INBOX / file
    if not p.exists():
        return {"ok": False, "error": "파일 없음"}
    text = p.read_text(encoding="utf-8", errors="ignore")
    h1 = re.findall(r"^# (.+)$", text, flags=re.M)
    h2 = re.findall(r"^## (.+)$", text, flags=re.M)
    problems = []
    if p.suffix.lower() != ".md":
        problems.append("확장자가 .md가 아님")
    if len(h1) != 1:
        problems.append("H1 제목이 1개가 아님")
    if len(h2) < 2:
        problems.append("H2 섹션이 2개 미만")
    if len(text.strip()) < 80:
        problems.append("내용이 너무 짧음")
    same = [m for m in load_metadata() if Path(m["source_file"]).name == p.name]
    return {"ok": not problems, "problems": problems, "chars": len(text), "title": h1[0] if h1 else None,
            "sections": h2, "existing_doc_id": same[0]["doc_id"] if same else None,
            "preview": text[:300]}


def propose_metadata(file):
    """파일명·제목·본문에서 메타데이터 후보를 만든다(규칙). 판단은 validate_metadata가 한다."""
    text = (INBOX / file).read_text(encoding="utf-8", errors="ignore")
    title = (re.findall(r"^# (.+)$", text, flags=re.M) or [""])[0]
    parts = Path(file).stem.split("_")
    year = int(parts[0]) if parts and parts[0].isdigit() else None
    region = parts[1] if len(parts) > 1 else None
    customer = next((c for c in CUSTOMER_EN if c in title), "전체")
    product = next((x for x in PRODUCT_EN if x in title), "전체")
    if "시장현황" in title:
        doc_type = "시장현황"
    elif "FAQ" in title:
        doc_type = "FAQ"
    elif "공지" in title:
        doc_type = "공지"
    else:
        doc_type = "제품전략"
    codes = sorted(set(re.findall(r"[A-Z]{2,}-[A-Z]+-\d{2}", text)))
    if doc_type == "시장현황":
        doc_id = f"{REGION_EN.get(region, region)}_{year}_MARKET"
    elif doc_type == "공지":
        doc_id = f"{REGION_EN.get(region, region)}_{year}_NOTICE"
    else:
        doc_id = f"{REGION_EN.get(region, region)}_{year}_{CUSTOMER_EN.get(customer, customer)}_{PRODUCT_EN.get(product, product)}"
        if doc_type == "FAQ":
            doc_id += "_FAQ"
    existing = read_file(file).get("existing_doc_id")
    return {"doc_id": existing or doc_id, "year": year, "region": region, "customer_type": customer,
            "product": product, "doc_type": doc_type, "product_code": codes[0] if len(codes) == 1 else ("" if not codes else codes[0]),
            "source_file": f"docs/{region}/{file}", "all_codes_in_text": codes}


def _norm(metadata):
    """LLM이 year를 "2026"(문자열)로 넘겨도 받아 준다."""
    m = dict(metadata)
    if isinstance(m.get("year"), str) and m["year"].isdigit():
        m["year"] = int(m["year"])
    return m


def validate_metadata(file, metadata):
    """규칙 검사. needs_approval 이유가 있으면 사람 승인 없이는 commit할 수 없다."""
    metadata = _norm(metadata)
    meta = load_metadata()
    errors, approval = [], []
    known_regions = {m["region"] for m in meta}
    known_years = {m["year"] for m in meta}
    if not isinstance(metadata.get("year"), int):
        errors.append("year가 정수가 아님")
    if not metadata.get("region"):
        errors.append("region 없음")
    if metadata.get("region") and metadata["region"] not in known_regions:
        approval.append(f"새 지역 '{metadata['region']}' — 질문 필터(common.REGIONS)도 이 지역을 모름")
    if isinstance(metadata.get("year"), int) and metadata["year"] not in known_years:
        approval.append(f"새 연도 {metadata['year']} — 질문 필터(common.YEARS)도 이 연도를 모름")
    existing = [m for m in meta if m["doc_id"] == metadata.get("doc_id")]
    if existing:
        approval.append(f"기존 문서 {metadata['doc_id']}를 덮어씀 (수정 반영)")
    code = metadata.get("product_code") or ""
    known_types = {m["doc_type"] for m in meta}
    if metadata.get("doc_type") not in known_types:
        approval.append(f"새 문서 유형 {metadata.get('doc_type')} — 기존 문서와 검색 경쟁 가능")
    if metadata.get("doc_type") == "제품전략" and not code:
        errors.append("제품전략 문서인데 product_code 없음")
    if code and metadata.get("year") and not code.endswith(str(metadata["year"])[-2:]):
        errors.append(f"제품코드 {code}의 연도와 year {metadata['year']} 불일치")
    other = [m["doc_id"] for m in meta if code and m["product_code"] == code and m["doc_id"] != metadata.get("doc_id")]
    if other and metadata.get("doc_type") == "제품전략":
        errors.append(f"제품코드 {code}를 이미 {other}가 사용")
    return {"ok": not errors, "errors": errors, "needs_approval": approval}


def stage_and_evaluate(file, metadata):
    """실제 반영 전에 '반영했다고 치고' Golden 20문항으로 회귀 평가한다. (라이브 인덱스는 건드리지 않음)"""
    metadata = _norm(metadata)
    meta = load_metadata()
    text = (INBOX / file).read_text(encoding="utf-8")
    base_sum, base_per = evaluate_chunks(build_chunks(meta))
    cand_meta = [m for m in meta if m["doc_id"] != metadata["doc_id"]] + [dict(metadata, year=int(metadata["year"]))]
    cand_sum, cand_per = evaluate_chunks(build_chunks(cand_meta, {metadata["doc_id"]: text}))
    changed = [{"query_id": q, "before": base_per[q]["top3"], "after": cand_per[q]["top3"],
                "rr": [round(base_per[q]["rr"], 3), round(cand_per[q]["rr"], 3)]}
               for q in base_per if base_per[q]["top3"] != cand_per[q]["top3"]]
    lost = [q for q in base_per if base_per[q]["hit"] > cand_per[q]["hit"]]
    reasons = []
    if base_sum["recall"] - cand_sum["recall"] > REGRESSION_RULES["recall_drop"]:
        reasons.append(f"Recall@3 {base_sum['recall']} → {cand_sum['recall']}")
    if base_sum["mrr"] - cand_sum["mrr"] > REGRESSION_RULES["mrr_drop"]:
        reasons.append(f"MRR {base_sum['mrr']} → {cand_sum['mrr']}")
    if len(lost) > REGRESSION_RULES["lost_hits"]:
        reasons.append(f"정답을 놓치게 된 질문 {lost}")
    st = load_state()
    st["files"].setdefault(file, {})
    st["files"][file].update({"sha1": _sha1(text), "status": "evaluated", "doc_id": metadata["doc_id"],
                              "eval": {"before": base_sum, "after": cand_sum, "regression": reasons}})
    save_state(st)
    return {"before": base_sum, "after": cand_sum, "regression": bool(reasons), "regression_reasons": reasons,
            "changed_queries": changed}


def request_approval(file, reason, approver=None):
    """사람에게 승인을 묻는다. approver: 'yes'/'no'를 돌려주는 함수(실행기에서 주입)."""
    answer = approver(file, reason) if approver else "no"
    st = load_state()
    st["approvals"][file] = {"reason": reason, "answer": answer, "t": time.strftime("%Y-%m-%d %H:%M:%S")}
    save_state(st)
    return {"approved": answer == "yes", "answer": answer}


def commit_document(file, metadata):
    """문서를 실제로 반영한다: docs/에 복사, metadata.csv 갱신, heading 청크 재생성.
    ── Guardrail (코드로 강제) ──
      1) 같은 파일·같은 내용으로 stage_and_evaluate를 먼저 했어야 함
      2) 검증 오류가 없어야 함
      3) 승인 필요 사유나 회귀가 있으면 사람 승인('yes')이 있어야 함"""
    metadata = _norm(metadata)
    st = load_state()
    text = (INBOX / file).read_text(encoding="utf-8")
    rec = st["files"].get(file, {})
    if rec.get("status") != "evaluated" or rec.get("sha1") != _sha1(text):
        return {"ok": False, "blocked": "평가(stage_and_evaluate)를 먼저 해야 합니다"}
    v = validate_metadata(file, metadata)
    if not v["ok"]:
        return {"ok": False, "blocked": f"검증 오류: {v['errors']}"}
    need = v["needs_approval"] + rec["eval"]["regression"]
    if need and st["approvals"].get(file, {}).get("answer") != "yes":
        return {"ok": False, "blocked": f"사람 승인이 필요합니다: {need}"}
    # --- 백업 (rollback용)
    st["version"] += 1
    bdir = STATE_DIR / "backups" / f"v{st['version']}"
    bdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(METADATA_CSV, bdir / "metadata.csv")
    dest = BASE_DIR / metadata["source_file"]
    if dest.exists():
        shutil.copy(dest, bdir / dest.name)
    # --- 반영
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(INBOX / file, dest)
    rows = [m for m in load_metadata() if m["doc_id"] != metadata["doc_id"]]
    rows.append({k: metadata.get(k, "") for k in ["doc_id", "year", "region", "customer_type", "product",
                                                  "doc_type", "product_code", "source_file"]})
    with open(METADATA_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id", "year", "region", "customer_type", "product",
                                          "doc_type", "product_code", "source_file"])
        w.writeheader(); w.writerows(rows)
    chunks = build_chunks(load_metadata())
    (OUT_DIR / "chunks_heading.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")
    st["files"][file].update({"status": "committed", "version": st["version"]})
    st["last_eval"] = rec["eval"]["after"]
    st["history"].append({"version": st["version"], "file": file, "doc_id": metadata["doc_id"],
                          "dest": metadata["source_file"], "new_file": not (bdir / dest.name).exists()})
    save_state(st)
    return {"ok": True, "version": st["version"], "doc_id": metadata["doc_id"], "chunks_total": len(chunks)}


def hold_file(file, reason):
    """보류: 반영하지 않고 이유를 Memory에 남긴다 (사람이 나중에 검토)."""
    st = load_state()
    st["files"].setdefault(file, {}).update({"status": "held", "reason": reason,
                                             "sha1": _sha1((INBOX / file).read_text(encoding="utf-8", errors="ignore"))})
    save_state(st)
    return {"ok": True, "status": "held"}


def reject_file(file, reason):
    """거부: 형식이 맞지 않는 등 처리 대상이 아님."""
    st = load_state()
    st["files"].setdefault(file, {}).update({"status": "rejected", "reason": reason,
                                             "sha1": _sha1((INBOX / file).read_text(encoding="utf-8", errors="ignore"))})
    save_state(st)
    return {"ok": True, "status": "rejected"}


def rollback_last(approver=None):
    """마지막 반영을 되돌린다. ── Guardrail: 항상 사람 승인 필요 ──"""
    st = load_state()
    if not st["history"]:
        return {"ok": False, "blocked": "되돌릴 반영 이력이 없습니다"}
    h = st["history"][-1]
    if (approver(h["file"], f"v{h['version']} 반영({h['doc_id']})을 되돌립니다") if approver else "no") != "yes":
        return {"ok": False, "blocked": "사람 승인이 없어 되돌리지 않았습니다"}
    bdir = STATE_DIR / "backups" / f"v{h['version']}"
    shutil.copy(bdir / "metadata.csv", METADATA_CSV)
    dest = BASE_DIR / h["dest"]
    if h["new_file"]:
        dest.unlink(missing_ok=True)
        if dest.parent.exists() and not any(dest.parent.iterdir()):
            dest.parent.rmdir()            # 새 지역 폴더가 비면 정리
    else:
        shutil.copy(bdir / dest.name, dest)
    chunks = build_chunks(load_metadata())
    (OUT_DIR / "chunks_heading.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")
    st["history"].pop()
    st["files"][h["file"]]["status"] = "rolled_back"
    save_state(st)
    return {"ok": True, "rolled_back": h["doc_id"], "chunks_total": len(chunks)}


def write_report(summary):
    """사람에게 보고서를 남긴다: agent_state/report.md"""
    st = load_state()
    lines = ["# Document Update Agent 실행 보고", "", summary, "", "| 파일 | 상태 | doc_id | 사유 |", "|---|---|---|---|"]
    for f, r in st["files"].items():
        reason = r.get("reason") or "; ".join(r.get("eval", {}).get("regression", [])) or ""
        lines.append(f"| {f} | {r.get('status')} | {r.get('doc_id', '')} | {reason} |")
    (STATE_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"ok": True, "path": "agent_state/report.md"}


# ------------------------------------------------------------ LLM에 알려 줄 Tool 설명 (OpenAI function calling)
def _fn(name, desc, props, required):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required}}}


_F = {"file": {"type": "string", "description": "inbox 안의 파일 이름"}}
_M = {"metadata": {"type": "object", "description": "propose_metadata가 돌려준 메타데이터(필요하면 수정)"}}
TOOL_SPECS = [
    _fn("list_inbox", "inbox 파일 목록과 이전 처리 이력(memory)을 본다.", {}, []),
    _fn("read_file", "파일 형식과 내용을 검사한다.", _F, ["file"]),
    _fn("propose_metadata", "파일에서 메타데이터 후보를 만든다.", _F, ["file"]),
    _fn("validate_metadata", "메타데이터를 검사한다. errors가 있으면 반영 불가, needs_approval이 있으면 사람 승인 필요.", {**_F, **_M}, ["file", "metadata"]),
    _fn("stage_and_evaluate", "반영했다고 가정하고 Golden 20문항으로 회귀 평가한다. commit 전에 반드시 실행.", {**_F, **_M}, ["file", "metadata"]),
    _fn("request_approval", "사람에게 승인을 요청한다. 새 지역·연도·유형, 기존 문서 덮어쓰기, 회귀가 있을 때.", {**_F, "reason": {"type": "string"}}, ["file", "reason"]),
    _fn("commit_document", "문서를 실제로 반영한다(docs·metadata·청크 갱신).", {**_F, **_M}, ["file", "metadata"]),
    _fn("hold_file", "반영하지 않고 보류한다(사람 검토 대기).", {**_F, "reason": {"type": "string"}}, ["file", "reason"]),
    _fn("reject_file", "처리 대상이 아닌 파일을 거부한다.", {**_F, "reason": {"type": "string"}}, ["file", "reason"]),
    _fn("write_report", "모든 파일 처리를 끝낸 뒤 보고서를 쓴다.", {"summary": {"type": "string"}}, ["summary"]),
]
