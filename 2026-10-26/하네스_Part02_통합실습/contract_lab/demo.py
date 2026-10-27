"""M1-03: 유효 요청·잘못된 완료 주장·변경된 입력 조건을 안전하게 비교한다."""
import json
from pathlib import Path
from .contracts import verify_delivery, validate_request

HERE = Path(__file__).resolve().parent
request = json.loads((HERE / "fixtures" / "request_ok.json").read_text(encoding="utf-8"))
cases = json.loads((HERE / "fixtures" / "candidates.json").read_text(encoding="utf-8"))
print("REQUEST CHECK", validate_request(request))
for name, candidate in cases.items():
    result = verify_delivery(request, candidate)
    print(f"{name:21s} {result['decision']:5s} {result['issues']}")

print("\n변경된 입력 계약도 검증해야 한다")
for minimum in (6000, 10000):
    changed = {**request, "min_total": minimum}
    if minimum == 6000:
        candidate = {**cases["pass"], "artifact_path": "contract_lab/fixtures/filtered_6000.csv",
                     "declared_count": 1, "declared_total": 6000}
    else:
        candidate = cases["pass"]  # 일부러 5000원 기준 파일을 그대로 제출
    result = verify_delivery(changed, candidate)
    print(f"min_total={minimum}: {result['decision']} {result['issues']}")
