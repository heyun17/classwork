---
name: order-report-check
description: Use when verifying the order report CSV, source integrity, or min_total filter after Python report changes. Do not use for unrelated documentation edits.
---

# 주문 보고서 검증 절차
1. 저장소의 `AGENTS.md` 완료 기준을 확인한다.
2. `python .agents/skills/order-report-check/scripts/check_report.py` 를 실행한다.
3. 실패 시 입력 원본을 수정하지 않고 어떤 검사와 기대값이 다른지 기록한다.
4. 호출되었다는 사실과 검증 통과를 혼동하지 않는다. 실제 명령 출력으로 확인한다.
5. 검사 실패를 숨긴 채 완료했다고 보고하지 않는다.
