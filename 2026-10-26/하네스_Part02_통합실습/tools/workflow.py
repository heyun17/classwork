"""교육용 명시적 Python 오케스트레이터. Codex 자체의 서브에이전트 호출 API가 아니다."""
import json
from pathlib import Path
from report import BASE, make_report
from tools.contract_check import verify_report


def run_workflow(min_total:int=5000)->dict:
    """선행 의존성: 구현 성공 -> 검증 성공 -> 완료 보고."""
    dest = BASE / "output" / "filtered_report.csv"
    count=make_report(BASE / "orders.csv",dest,min_total=min_total)
    result=verify_report(dest,min_total)
    return {"step":"verify","generated_count":count,**result,
            "decision":"PASS" if result["ok"] else "BLOCK"}

if __name__ == "__main__":
    print(json.dumps(run_workflow(),ensure_ascii=False,indent=2))
