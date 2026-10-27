"""M1-04: 계약 결과를 게이트로 사용하는 결정적 오케스트레이션 시뮬레이터.

주요 제약:
- 현재 수업의 단계는 파일을 수정하거나 서비스에 공개하지 않는다.
- 병렬 감사는 읽기 전용이며, Codex 서브에이전트 실행을 의미하지 않는다.
- 검증 실패는 재시도하지 않고, 일시 장애만 최대 2회 시도한다.
"""
from __future__ import annotations

import csv
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from contract_lab.contracts import COLUMNS_RESULT, ROOT, validate_request, verify_delivery

FIXTURES = ROOT / "contract_lab" / "fixtures"


class TemporaryAuditError(RuntimeError):
    """교육용 외부 감사 도구의 일시적 실패."""


def load_case(name: str) -> tuple[dict, dict]:
    cases = json.loads((FIXTURES / "candidates.json").read_text(encoding="utf-8"))
    if name not in cases and name != "bad_request":
        raise ValueError(f"존재하지 않는 사례: {name}")
    request = json.loads((FIXTURES / "request_ok.json").read_text(encoding="utf-8"))
    if name == "bad_request":
        request["min_total"] = True  # bool은 int의 하위 타입이지만 계약은 금지
        return request, cases["pass"]
    return request, cases[name]


def _schema_audit(candidate: dict) -> str:
    """후보 산출물의 정확한 열 스키마만 다시 확인(읽기 전용 감사)."""
    relative = candidate["artifact_path"]
    # 경로 검증은 선행 verify_delivery에서 끝난 경우에만 호출해야 한다.
    path = (ROOT / relative).resolve()
    with path.open(encoding="utf-8-sig", newline="") as file:
        fieldnames = csv.DictReader(file).fieldnames
    if fieldnames != COLUMNS_RESULT:
        raise ValueError("출력 열 구조가 계약과 다름")
    return "출력 스키마 일치"


def _source_audit(fault: str, attempt: int) -> str:
    """원본 무결성 감사와 교육용 일시 장애 주입."""
    if fault == "temporary" and attempt == 1:
        raise TemporaryAuditError("첫 시도에서 감사 도구가 일시적으로 응답하지 않음")
    if fault == "persistent":
        raise TemporaryAuditError("감사 도구가 계속 응답하지 않음")
    if fault == "invalid":
        raise ValueError("참조 데이터 계약 자체가 잘못됨")
    if fault not in {"none", "temporary", "persistent", "invalid"}:
        raise ValueError("정의되지 않은 장애 시나리오")
    actual = hashlib.sha256((ROOT / "orders.csv").read_bytes()).hexdigest()
    trusted = (ROOT / "data" / "source.sha256").read_text(encoding="utf-8").strip()
    if actual != trusted:
        raise ValueError("원본 무결성 불일치")
    return "원본 데이터 해시 일치"


def _run_with_retry(fn, max_attempts: int = 2):
    """일시 장애만 재시도. 논리 오류/계약 위반은 즉시 실패."""
    for attempt in range(1, max_attempts + 1):
        try:
            message = fn(attempt)
            return {"status": "PASS", "attempts": attempt, "note": message}
        except TemporaryAuditError as exc:
            if attempt == max_attempts:
                return {"status": "BLOCK", "attempts": attempt, "note": str(exc)}
        except (ValueError, OSError, csv.Error) as exc:
            return {"status": "BLOCK", "attempts": attempt, "note": str(exc)}
    raise AssertionError("재시도 종료 오류")


def run_case(case: str = "pass", fault: str = "none") -> dict:
    """단계 의존성·게이트·병렬 읽기·재시도 여부를 추적한다."""
    if fault not in {"none", "temporary", "persistent", "invalid"}:
        raise ValueError("지원하지 않는 fault")
    req, candidate = load_case(case)
    stages = {name: "SKIP" for name in
              ("intake", "contract_gate", "schema_review", "source_review", "release_gate")}
    events: list[str] = []

    errors = validate_request(req)
    stages["intake"] = "PASS" if not errors else "BLOCK"
    events.append(f"intake={stages['intake']}")
    if errors:
        events.append("contract_gate 이후: SKIP (선행 요청 유효성 실패)")
        return {"decision": "BLOCK", "stages": stages, "events": events,
                "issues": errors, "audits": {}, "released": False}

    contract = verify_delivery(req, candidate)
    stages["contract_gate"] = contract["decision"]
    events.append(f"contract_gate={contract['decision']}")
    if contract["decision"] != "PASS":
        events.append("읽기 전용 감사·최종 승인은 실행하지 않음")
        return {"decision": "BLOCK", "stages": stages, "events": events,
                "issues": contract["issues"], "audits": {}, "released": False}

    # 계약을 통과한 산출물에 대해서만 독립 읽기 감사 2개를 병렬 수행한다.
    # '병렬'은 실제 작업이 겹쳐 실행된다는 뜻이지 에이전트 2개 생성이 아니다.
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            "schema_review": pool.submit(_run_with_retry, lambda attempt: _schema_audit(candidate)),
            "source_review": pool.submit(_run_with_retry, lambda attempt: _source_audit(fault, attempt)),
        }
        audits = {key: futures[key].result() for key in ("schema_review", "source_review")}
    for key, result in audits.items():
        stages[key] = result["status"]
        events.append(f"{key}={result['status']} attempts={result['attempts']}")

    passed = all(x["status"] == "PASS" for x in audits.values())
    stages["release_gate"] = "PASS" if passed else "BLOCK"
    events.append("release_gate=PASS (실제 배포 없음)" if passed else "release_gate=BLOCK (공개 중단)")
    return {"decision": "PASS" if passed else "BLOCK", "stages": stages,
            "events": events, "issues": [v["note"] for v in audits.values() if v["status"] != "PASS"],
            "audits": audits, "released": False}
