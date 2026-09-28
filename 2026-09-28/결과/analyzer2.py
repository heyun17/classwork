# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BASE_DIR / "prompt.md"
PACKET_SUMMARY_PATH = BASE_DIR / "packet_summary.json"

DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_OUTPUT = "diagnosis_google.json"
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_WAIT = 5.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "prompt.md와 packet_summary.json을 읽고 "
            "각 장애를 Gemini API로 1회씩 독립 분석합니다."
        )
    )
    parser.add_argument(
        "--api-key-env",
        default="GEMINI_API_KEY",
        help=(
            "Gemini API 키가 저장된 환경변수 이름 "
            "(예: GEMINI_API_KEY_EXTRACT1)"
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"사용할 Gemini 모델 (기본값: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"결과 JSON 파일명 (기본값: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=(
            "HTTP 500/503 발생 시 최대 재시도 횟수 "
            f"(기본값: {DEFAULT_MAX_RETRIES})"
        ),
    )
    parser.add_argument(
        "--retry-wait",
        type=float,
        default=DEFAULT_RETRY_WAIT,
        help=(
            "첫 재시도 전 대기 시간(초). 재시도마다 대기 시간이 증가합니다. "
            f"(기본값: {DEFAULT_RETRY_WAIT})"
        ),
    )
    return parser.parse_args()


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path.name}")
    return path.read_text(encoding="utf-8-sig")


def load_packet_cases(path: Path) -> list[dict[str, Any]]:
    raw = load_text(path)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path.name}의 JSON 형식이 올바르지 않습니다: "
            f"line {exc.lineno}, column {exc.colno}"
        ) from exc

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(
            f"{path.name}에 비어 있지 않은 'cases' 배열이 필요합니다."
        )

    seen_case_ids: set[str] = set()

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}]가 JSON object가 아닙니다.")

        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"cases[{index}]에 유효한 case_id가 없습니다.")

        if case_id in seen_case_ids:
            raise ValueError(f"중복 case_id가 있습니다: {case_id}")

        seen_case_ids.add(case_id)

    return cases


def render_prompt(
    prompt_template: str,
    case: dict[str, Any],
) -> str:
    placeholder = "{{PACKET_SUMMARY}}"

    if placeholder not in prompt_template:
        raise ValueError(
            f"{PROMPT_PATH.name}에서 "
            f"{placeholder} 자리표시자를 찾을 수 없습니다."
        )

    packet_json = json.dumps(
        case,
        ensure_ascii=False,
        indent=2,
    )

    return prompt_template.replace(
        placeholder,
        packet_json,
    )


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini 응답을 JSON으로 해석하지 못했습니다.\n"
            f"원본 응답:\n{text}"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini 응답의 최상위 값이 JSON object가 아닙니다."
        )

    return result


def is_retryable_server_error(exc: Exception) -> bool:
    """
    Gemini API의 일시적 서버 오류(HTTP 500/503)인지 판별한다.
    SDK 예외 객체의 속성과 문자열 메시지를 모두 확인한다.
    """
    candidates = [
        getattr(exc, "code", None),
        getattr(exc, "status_code", None),
        getattr(exc, "status", None),
    ]

    for value in candidates:
        if value in (500, 503, "500", "503"):
            return True

    text = str(exc).upper()

    return (
        "500" in text
        or "503" in text
        or "INTERNAL" in text
        or "UNAVAILABLE" in text
    )


def analyze_case_once(
    client: genai.Client,
    model: str,
    prompt_template: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    case_id = case["case_id"]
    prompt = render_prompt(
        prompt_template,
        case,
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    response_text = (response.text or "").strip()

    if not response_text:
        raise RuntimeError(
            f"{case_id}: Gemini가 빈 응답을 반환했습니다."
        )

    result = extract_json(response_text)

    returned_case_id = result.get("case_id")
    if returned_case_id != case_id:
        raise ValueError(
            f"{case_id}: Gemini 응답의 case_id가 일치하지 않습니다. "
            f"응답값={returned_case_id!r}"
        )

    return result


def analyze_case_with_retry(
    client: genai.Client,
    model: str,
    prompt_template: str,
    case: dict[str, Any],
    max_retries: int,
    retry_wait: float,
) -> dict[str, Any]:
    case_id = case["case_id"]
    total_attempts = 1 + max(0, max_retries)

    for attempt in range(1, total_attempts + 1):
        print(f"[분석 시작] {case_id} (시도 {attempt}/{total_attempts})")

        try:
            result = analyze_case_once(
                client=client,
                model=model,
                prompt_template=prompt_template,
                case=case,
            )
            print(f"[분석 완료] {case_id}")
            return result

        except Exception as exc:
            retryable = is_retryable_server_error(exc)
            is_last = attempt >= total_attempts

            if not retryable or is_last:
                raise

            # 5, 10, 20, 30, ...초로 증가하되 30초를 넘기지 않는다.
            wait_seconds = min(
                retry_wait * (2 ** (attempt - 1)),
                30.0,
            )

            print(
                f"[일시적 서버 오류] {case_id}: "
                f"{type(exc).__name__}: {exc}"
            )
            print(
                f"[재시도 대기] {wait_seconds:.0f}초 후 다시 시도합니다."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        f"{case_id}: 재시도 루프가 비정상 종료되었습니다."
    )


def load_existing_results(
    output_path: Path,
    provider: str,
    model: str,
) -> list[dict[str, Any]]:
    """
    기존 diagnosis_google.json이 있으면 완료된 case 결과를 읽어서 이어서 진행한다.
    provider/model이 현재 실행값과 다르면 안전을 위해 이어쓰지 않는다.
    """
    if not output_path.exists():
        return []

    try:
        data = json.loads(
            output_path.read_text(encoding="utf-8-sig")
        )
    except Exception as exc:
        raise ValueError(
            f"기존 {output_path.name}을 읽지 못했습니다: {exc}"
        ) from exc

    existing_provider = data.get("provider")
    existing_model = data.get("model")
    diagnoses = data.get("diagnoses")

    if existing_provider != provider:
        raise ValueError(
            f"기존 {output_path.name}의 provider가 "
            f"{existing_provider!r}입니다. 현재 provider={provider!r}와 다릅니다."
        )

    if existing_model != model:
        raise ValueError(
            f"기존 {output_path.name}의 model이 "
            f"{existing_model!r}입니다. 현재 model={model!r}와 다릅니다.\n"
            "같은 출력 파일로 이어서 실행하려면 동일한 --model을 사용하세요."
        )

    if not isinstance(diagnoses, list):
        raise ValueError(
            f"기존 {output_path.name}의 diagnoses 형식이 올바르지 않습니다."
        )

    valid_results: list[dict[str, Any]] = []

    for item in diagnoses:
        if (
            isinstance(item, dict)
            and isinstance(item.get("case_id"), str)
            and item.get("case_id")
        ):
            valid_results.append(item)

    return valid_results


def save_progress(
    output_path: Path,
    provider: str,
    model: str,
    diagnoses: list[dict[str, Any]],
) -> None:
    output = {
        "provider": provider,
        "model": model,
        "diagnoses": diagnoses,
    }

    output_path.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()

    api_key_env = args.api_key_env.strip()
    api_key = os.getenv(api_key_env, "").strip()
    model = args.model.strip()
    output_path = BASE_DIR / args.output

    if not api_key_env:
        print("[오류] --api-key-env 값이 비어 있습니다.")
        sys.exit(1)

    if not api_key:
        print(
            f"[오류] 환경변수 {api_key_env}에서 "
            "Gemini API 키를 찾지 못했습니다."
        )
        sys.exit(1)

    if args.max_retries < 0:
        print("[오류] --max-retries는 0 이상이어야 합니다.")
        sys.exit(1)

    if args.retry_wait < 0:
        print("[오류] --retry-wait는 0 이상이어야 합니다.")
        sys.exit(1)

    try:
        prompt_template = load_text(PROMPT_PATH)
        cases = load_packet_cases(PACKET_SUMMARY_PATH)
        diagnoses = load_existing_results(
            output_path=output_path,
            provider="google",
            model=model,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"[오류] {exc}")
        sys.exit(1)

    completed_case_ids = {
        item["case_id"]
        for item in diagnoses
    }

    print(f"Prompt : {PROMPT_PATH.name}")
    print(f"Input  : {PACKET_SUMMARY_PATH.name}")
    print(f"Model  : {model}")
    print(f"API Key: {api_key_env}")
    print(f"Cases  : {len(cases)}개")
    print(f"완료됨 : {len(completed_case_ids)}개")
    print(f"재시도 : 500/503 발생 시 최대 {args.max_retries}회")
    print()

    if completed_case_ids:
        print(
            "[이어하기] 기존 결과가 있어 완료된 case는 건너뜁니다: "
            + ", ".join(sorted(completed_case_ids))
        )
        print()

    client = genai.Client(api_key=api_key)

    try:
        for case in cases:
            case_id = case["case_id"]

            if case_id in completed_case_ids:
                print(f"[건너뜀] {case_id} - 기존 결과 있음")
                continue

            result = analyze_case_with_retry(
                client=client,
                model=model,
                prompt_template=prompt_template,
                case=case,
                max_retries=args.max_retries,
                retry_wait=args.retry_wait,
            )

            diagnoses.append(result)
            completed_case_ids.add(case_id)

            # 성공한 case는 즉시 파일에 저장한다.
            # 이후 500/503이나 다른 오류가 발생해도 완료된 결과는 남는다.
            save_progress(
                output_path=output_path,
                provider="google",
                model=model,
                diagnoses=diagnoses,
            )

            print(
                f"[진행 저장] {case_id} 결과를 "
                f"{output_path.name}에 저장했습니다."
            )
            print()

    except Exception as exc:
        print()
        print(
            f"[오류] 분석 중 중단되었습니다: "
            f"{type(exc).__name__}: {exc}"
        )
        print(
            f"이미 완료된 결과는 {output_path.name}에 저장되어 있습니다."
        )
        print(
            "같은 명령으로 다시 실행하면 완료된 case는 건너뛰고 이어서 진행합니다."
        )
        sys.exit(1)

    # 이미 전부 완료된 상태에서 실행한 경우에도 파일을 한 번 정리해서 저장한다.
    save_progress(
        output_path=output_path,
        provider="google",
        model=model,
        diagnoses=diagnoses,
    )

    print()
    print("=" * 60)
    print(
        f"완료: {len(diagnoses)}개 장애 결과가 저장되어 있습니다."
    )
    print(f"저장: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
