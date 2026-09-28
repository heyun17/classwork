# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
PROMPT_PATH = BASE_DIR / "prompt.md"
PACKET_SUMMARY_PATH = BASE_DIR / "packet_summary.json"
OUTPUT_PATH = BASE_DIR / "diagnosis.json"

DEFAULT_MODEL = "gpt-5.6-luna"


def load_env_file(path: Path) -> None:
    """
    python-dotenv 없이 .env 파일을 직접 읽는다.
    KEY=VALUE 형태만 사용하며, 빈 줄과 # 주석은 무시한다.
    """
    if not path.exists():
        raise FileNotFoundError(f".env 파일을 찾을 수 없습니다: {path}")

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        if key:
            os.environ.setdefault(key, value)


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
        raise ValueError(f"{path.name}에 비어 있지 않은 'cases' 배열이 필요합니다.")

    seen_case_ids: set[str] = set()

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index - 1}]가 JSON object가 아닙니다.")

        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"cases[{index - 1}]에 유효한 case_id가 없습니다.")

        if case_id in seen_case_ids:
            raise ValueError(f"중복 case_id가 있습니다: {case_id}")
        seen_case_ids.add(case_id)

    return cases


def render_prompt(prompt_template: str, case: dict[str, Any]) -> str:
    placeholder = "{{PACKET_SUMMARY}}"

    if placeholder not in prompt_template:
        raise ValueError(
            f"{PROMPT_PATH.name}에서 {placeholder} 자리표시자를 찾을 수 없습니다."
        )

    packet_json = json.dumps(case, ensure_ascii=False, indent=2)
    return prompt_template.replace(placeholder, packet_json)


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "AI 응답을 JSON으로 해석하지 못했습니다.\n"
            f"원본 응답:\n{text}"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("AI 응답의 최상위 값이 JSON object가 아닙니다.")

    return result


def analyze_case(
    client: OpenAI,
    model: str,
    prompt_template: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    case_id = case["case_id"]
    prompt = render_prompt(prompt_template, case)

    print(f"[분석 시작] {case_id}")

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    response_text = response.output_text.strip()
    if not response_text:
        raise RuntimeError(f"{case_id}: AI가 빈 응답을 반환했습니다.")

    result = extract_json(response_text)

    returned_case_id = result.get("case_id")
    if returned_case_id != case_id:
        raise ValueError(
            f"{case_id}: AI 응답의 case_id가 일치하지 않습니다. "
            f"응답값={returned_case_id!r}"
        )

    print(f"[분석 완료] {case_id}")
    return result


def main() -> None:
    try:
        load_env_file(ENV_PATH)
    except FileNotFoundError as exc:
        print(f"[오류] {exc}")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    if not api_key:
        print("[오류] .env에서 OPENAI_API_KEY를 찾지 못했습니다.")
        print(f"확인할 파일: {ENV_PATH}")
        sys.exit(1)

    try:
        prompt_template = load_text(PROMPT_PATH)
        cases = load_packet_cases(PACKET_SUMMARY_PATH)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[오류] {exc}")
        sys.exit(1)

    print(f"Prompt : {PROMPT_PATH.name}")
    print(f"Input  : {PACKET_SUMMARY_PATH.name}")
    print(f"Model  : {model}")
    print(f"Cases  : {len(cases)}개")
    print()

    client = OpenAI(api_key=api_key)
    diagnoses: list[dict[str, Any]] = []

    try:
        for case in cases:
            diagnoses.append(
                analyze_case(
                    client=client,
                    model=model,
                    prompt_template=prompt_template,
                    case=case,
                )
            )
    except Exception as exc:
        print()
        print(f"[오류] 분석 중 중단되었습니다: {exc}")
        print("diagnosis.json은 작성하지 않았습니다.")
        sys.exit(1)

    output = {
        "model": model,
        "diagnoses": diagnoses,
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print(f"완료: {len(diagnoses)}개 장애를 각각 1회씩 분석했습니다.")
    print(f"저장: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
