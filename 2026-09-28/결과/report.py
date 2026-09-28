# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "diagnosis.json"
OUTPUT_PATH = BASE_DIR / "ai_report.html"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_list(items: list[Any] | None) -> str:
    if not items:
        return "<p class='muted'>없음</p>"

    rows = "\n".join(f"<li>{esc(item)}</li>" for item in items)
    return f"<ul>{rows}</ul>"


def render_evidence(evidence: list[dict[str, Any]] | None) -> str:
    if not evidence:
        return "<p class='muted'>관찰 근거 없음</p>"

    rows = []
    for item in evidence:
        observation = esc(item.get("observation", ""))
        meaning = esc(item.get("meaning", ""))
        rows.append(
            f"""
            <tr>
              <td>{observation}</td>
              <td>{meaning}</td>
            </tr>
            """
        )

    return f"""
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>관찰 내용</th>
            <th>의미</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    """


def render_cause(cause: dict[str, Any], index: int) -> str:
    cause_name = esc(cause.get("cause", ""))
    reasoning = esc(cause.get("reasoning", ""))

    return f"""
    <section class="cause-card">
      <div class="cause-title">
        <span class="badge">후보 {index}</span>
        <h4>{cause_name}</h4>
      </div>

      <div class="cause-grid">
        <div>
          <h5>근거</h5>
          {render_list(cause.get("evidence"))}
        </div>

        <div>
          <h5>추론</h5>
          <p>{reasoning}</p>
        </div>

        <div>
          <h5>확인 방법</h5>
          {render_list(cause.get("verification"))}
        </div>

        <div>
          <h5>조치</h5>
          {render_list(cause.get("action"))}
        </div>
      </div>
    </section>
    """


def render_case(case: dict[str, Any]) -> str:
    case_id = esc(case.get("case_id", "unknown"))
    summary = esc(case.get("summary", ""))
    failure_point = esc(case.get("failure_point", ""))

    causes = case.get("possible_causes") or []
    cause_html = "".join(
        render_cause(cause, index)
        for index, cause in enumerate(causes, start=1)
    )

    return f"""
    <article class="case-card">
      <header class="case-header">
        <div>
          <span class="case-id">{case_id}</span>
          <h2>{case_id} 분석 결과</h2>
        </div>
      </header>

      <section class="summary-grid">
        <div class="summary-box">
          <h3>요약</h3>
          <p>{summary}</p>
        </div>

        <div class="summary-box">
          <h3>실패 지점</h3>
          <p>{failure_point}</p>
        </div>
      </section>

      <section>
        <h3>패킷 근거</h3>
        {render_evidence(case.get("evidence"))}
      </section>

      <section>
        <h3>원인 후보 · 확인 방법 · 조치</h3>
        {cause_html if cause_html else "<p class='muted'>원인 후보 없음</p>"}
      </section>
    </article>
    """


def build_html(data: dict[str, Any]) -> str:
    model = esc(data.get("model", "unknown"))
    diagnoses = data.get("diagnoses") or []

    case_html = "".join(render_case(case) for case in diagnoses)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Network Diagnosis Report</title>

  <style>
    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: Arial, "Noto Sans KR", sans-serif;
      background: #f4f6f8;
      color: #20252b;
      line-height: 1.6;
    }}

    .container {{
      width: min(1180px, calc(100% - 32px));
      margin: 32px auto 60px;
    }}

    .top {{
      background: white;
      border: 1px solid #dfe3e8;
      border-radius: 14px;
      padding: 28px;
      margin-bottom: 24px;
    }}

    .top h1 {{
      margin: 0 0 8px;
      font-size: 28px;
    }}

    .top p {{
      margin: 4px 0;
      color: #58616b;
    }}

    .model {{
      display: inline-block;
      margin-top: 10px;
      padding: 6px 10px;
      border: 1px solid #cfd6dd;
      border-radius: 999px;
      font-size: 14px;
      background: #fafbfc;
    }}

    .case-card {{
      background: white;
      border: 1px solid #dfe3e8;
      border-radius: 14px;
      padding: 28px;
      margin-bottom: 24px;
    }}

    .case-header {{
      border-bottom: 1px solid #e5e9ed;
      padding-bottom: 16px;
      margin-bottom: 22px;
    }}

    .case-header h2 {{
      margin: 6px 0 0;
      font-size: 24px;
    }}

    .case-id {{
      display: inline-block;
      padding: 4px 9px;
      border-radius: 6px;
      background: #eef1f4;
      font-size: 13px;
      font-weight: 700;
    }}

    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}

    .summary-box {{
      border: 1px solid #e1e5e9;
      border-radius: 10px;
      padding: 18px;
      background: #fafbfc;
    }}

    h3 {{
      margin-top: 28px;
      margin-bottom: 12px;
      font-size: 19px;
    }}

    h4 {{
      margin: 0;
      font-size: 18px;
    }}

    h5 {{
      margin: 0 0 8px;
      font-size: 15px;
    }}

    p {{
      margin: 8px 0;
    }}

    ul {{
      margin: 8px 0 0;
      padding-left: 20px;
    }}

    li {{
      margin-bottom: 6px;
    }}

    .table-wrap {{
      overflow-x: auto;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
    }}

    th,
    td {{
      border: 1px solid #dfe3e8;
      padding: 12px 14px;
      text-align: left;
      vertical-align: top;
    }}

    th {{
      background: #f2f4f6;
    }}

    .cause-card {{
      border: 1px solid #dde2e7;
      border-radius: 10px;
      padding: 18px;
      margin-top: 14px;
    }}

    .cause-title {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
    }}

    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 6px;
      background: #eef1f4;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}

    .cause-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}

    .cause-grid > div {{
      border-top: 1px solid #eceff2;
      padding-top: 12px;
    }}

    .muted {{
      color: #77818c;
    }}

    footer {{
      text-align: center;
      color: #7a848e;
      font-size: 13px;
      margin-top: 24px;
    }}

    @media (max-width: 760px) {{
      .summary-grid,
      .cause-grid {{
        grid-template-columns: 1fr;
      }}

      .container {{
        width: min(100% - 20px, 1180px);
        margin-top: 16px;
      }}

      .top,
      .case-card {{
        padding: 20px;
      }}
    }}
  </style>
</head>

<body>
  <main class="container">
    <section class="top">
      <h1>AI Network Diagnosis Report</h1>
      <p>패킷 관찰 결과를 기반으로 생성한 네트워크 장애 분석 보고서</p>
      <span class="model">Model: {model}</span>
    </section>

    {case_html}

    <footer>
      Generated from diagnosis.json
    </footer>
  </main>
</body>
</html>
"""


def main() -> None:
    if not INPUT_PATH.exists():
        print(f"[오류] {INPUT_PATH.name} 파일을 찾을 수 없습니다.")
        print(f"현재 폴더: {BASE_DIR}")
        sys.exit(1)

    try:
        data = json.loads(INPUT_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(
            f"[오류] {INPUT_PATH.name}의 JSON 형식이 올바르지 않습니다. "
            f"line {exc.lineno}, column {exc.colno}"
        )
        sys.exit(1)

    diagnoses = data.get("diagnoses")
    if not isinstance(diagnoses, list) or not diagnoses:
        print(f"[오류] {INPUT_PATH.name}에 비어 있지 않은 diagnoses 배열이 필요합니다.")
        sys.exit(1)

    report = build_html(data)
    OUTPUT_PATH.write_text(report, encoding="utf-8")

    print(f"완료: {len(diagnoses)}개 장애 보고서를 생성했습니다.")
    print(f"저장: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
