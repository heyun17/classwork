"""Part 02 M1-03: 에이전트의 '완료' 주장과 실제 결과를 독립적으로 검증한다.

실습 계약의 의도: 원본 CSV는 신뢰 기준, output/·fixtures/는 검사 대상 파일.
학습용 코드이며 실제 운영의 권한/원본 신뢰 구축까지 대체하지 않는다.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FIELDS = {"schema_version", "request_id", "source_file", "min_total", "preserve_default"}
CANDIDATE_FIELDS = {"schema_version", "request_id", "status", "artifact_path", "declared_count", "declared_total", "ok"}
COLUMNS_SOURCE = ["order_id", "product", "quantity", "unit_price"]
COLUMNS_RESULT = [*COLUMNS_SOURCE, "total_amount"]


def validate_request(request: object) -> list[str]:
    """요청이 유효한지 확인한다. 예외 대신 검증 오류 코드를 반환한다."""
    if not isinstance(request, dict):
        return ["REQUEST_NOT_OBJECT"]
    errors: list[str] = []
    if set(request) != EXPECTED_FIELDS:
        errors.append("REQUEST_FIELDS_INVALID")
    if request.get("schema_version") != "1.0":
        errors.append("SCHEMA_VERSION_UNSUPPORTED")
    if not isinstance(request.get("request_id"), str) or not request["request_id"].strip():
        errors.append("REQUEST_ID_INVALID")
    if request.get("source_file") != "orders.csv":
        errors.append("SOURCE_NOT_ALLOWED")
    minimum = request.get("min_total")
    if type(minimum) is not int or minimum < 0:  # bool이 int의 하위 타입이라는 점에 주의
        errors.append("THRESHOLD_INVALID")
    if request.get("preserve_default") is not True:
        errors.append("DEFAULT_BEHAVIOR_REQUIRED")
    return errors


def _resolve_output(raw: object) -> Path | None:
    """임의 파일을 열지 않도록 산출물 읽기 경로를 허용 폴더로 한정한다."""
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts:
        return None
    if Path(raw).suffix.lower() != ".csv":
        return None
    path = (ROOT / raw).resolve()
    allowed = [(ROOT / "output").resolve(), (ROOT / "contract_lab" / "fixtures").resolve()]
    return path if any(path.is_relative_to(folder) for folder in allowed) else None


def _read_expected_rows(min_total: int) -> list[dict[str, str]]:
    """Codex가 작성한 산출물에서 정답을 추출하지 않는다. 신뢰 원본+업무식으로 계산한다."""
    with (ROOT / "orders.csv").open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS_SOURCE:
            raise ValueError("SOURCE_COLUMNS_INVALID")
        rows = list(reader)
    seen: set[str] = set()
    expected: list[dict[str, str]] = []
    for row in rows:
        order_id = row["order_id"]
        if not order_id or order_id in seen:
            raise ValueError("SOURCE_IDS_INVALID")
        seen.add(order_id)
        quantity, price = int(row["quantity"]), int(row["unit_price"])
        if quantity < 0 or price < 0:
            raise ValueError("SOURCE_NEGATIVE_VALUE")
        amount = quantity * price
        if amount >= min_total:
            expected.append({**row, "total_amount": str(amount)})
    return expected


def verify_delivery(request: object, candidate: object) -> dict:
    """요청·산출물·업무 정답·부작용을 구분하여 PASS/BLOCK을 반환한다."""
    keys = ("request_valid", "response_schema", "request_id_match", "artifact_present",
            "output_ids_match", "output_rows_match", "output_total_match",
            "reported_values_match", "source_unchanged")
    checks = {key: False for key in keys}
    issues = validate_request(request)
    checks["request_valid"] = not issues
    if issues:
        return {"decision": "BLOCK", "checks": checks, "issues": issues}
    assert isinstance(request, dict)

    if not isinstance(candidate, dict):
        return {"decision": "BLOCK", "checks": checks, "issues": ["RESPONSE_NOT_OBJECT"]}
    checks["response_schema"] = (
        set(candidate) == CANDIDATE_FIELDS
        and candidate.get("schema_version") == "1.0"
        and candidate.get("status") == "completed"
        and type(candidate.get("declared_count")) is int
        and candidate["declared_count"] >= 0
        and type(candidate.get("declared_total")) is int
        and candidate["declared_total"] >= 0
        and type(candidate.get("ok")) is bool
        and isinstance(candidate.get("request_id"), str)
        and isinstance(candidate.get("artifact_path"), str)
    )
    if not checks["response_schema"]:
        issues.append("RESPONSE_SCHEMA_INVALID")
    if candidate.get("ok") is not True:
        issues.append("CANDIDATE_NOT_COMPLETED")
    checks["request_id_match"] = candidate.get("request_id") == request["request_id"]
    if not checks["request_id_match"]:
        issues.append("REQUEST_ID_MISMATCH")

    path = _resolve_output(candidate.get("artifact_path"))
    checks["artifact_present"] = bool(path is not None and path.is_file())
    if not checks["artifact_present"]:
        issues.append("ARTIFACT_INVALID_OR_MISSING")

    try:
        digest = hashlib.sha256((ROOT / "orders.csv").read_bytes()).hexdigest()
        known_digest = (ROOT / "data" / "source.sha256").read_text(encoding="utf-8").strip()
        checks["source_unchanged"] = digest == known_digest
        if not checks["source_unchanged"]:
            issues.append("SOURCE_CHANGED")
    except OSError:
        issues.append("SOURCE_UNAVAILABLE")

    if not checks["source_unchanged"]:
        return {"decision": "BLOCK", "checks": checks, "issues": issues}

    if checks["artifact_present"]:
        try:
            expected = _read_expected_rows(request["min_total"])
            # 5000원 기본 과제에 대해서는 사전에 작성한 별도 정답셋과도 대조한다.
            fixed = json.loads((ROOT / "data" / "expected.json").read_text(encoding="utf-8"))
            if request["min_total"] == fixed["min_total"]:
                if ([r["order_id"] for r in expected] != fixed["filtered_ids"]
                    or sum(int(r["total_amount"]) for r in expected) != fixed["filtered_total"]):
                    raise ValueError("REFERENCE_DATA_MISMATCH")
            with path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != COLUMNS_RESULT:
                    raise ValueError("OUTPUT_COLUMNS_INVALID")
                rows = list(reader)
            ids = [r["order_id"] for r in rows]
            if len(ids) != len(set(ids)):
                raise ValueError("DUPLICATE_ORDER_ID")
            # 산출물 행마다 수량×단가를 검사한다. 합계가 같아도 행 값이 틀리면 BLOCK.
            for row in rows:
                q, p, amount = int(row["quantity"]), int(row["unit_price"]), int(row["total_amount"])
                if q < 0 or p < 0 or amount < 0 or q * p != amount:
                    issues.append("ROW_TOTAL_MISMATCH")
                    break
            actual_total = sum(int(r["total_amount"]) for r in rows)
            expected_total = sum(int(r["total_amount"]) for r in expected)
            checks["output_ids_match"] = ids == [r["order_id"] for r in expected]
            checks["output_rows_match"] = rows == expected and "ROW_TOTAL_MISMATCH" not in issues
            checks["output_total_match"] = actual_total == expected_total
            checks["reported_values_match"] = (
                len(rows) == candidate.get("declared_count")
                and actual_total == candidate.get("declared_total")
            )
            for flag, error in (("output_ids_match", "IDS_MISMATCH"),
                                ("output_rows_match", "ROW_VALUES_MISMATCH"),
                                ("output_total_match", "TOTAL_MISMATCH"),
                                ("reported_values_match", "DECLARATION_MISMATCH")):
                if not checks[flag]:
                    issues.append(error)
        except (OSError, KeyError, TypeError, ValueError, UnicodeError, csv.Error, json.JSONDecodeError) as exc:
            issues.append(f"OUTPUT_DATA_INVALID:{exc}")
    return {"decision": "PASS" if all(checks.values()) and not issues else "BLOCK",
            "checks": checks, "issues": issues}
