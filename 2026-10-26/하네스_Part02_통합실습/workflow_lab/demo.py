"""python -m workflow_lab.demo --case pass --fault temporary"""
import argparse
import json
from workflow_lab.runner import run_case

parser = argparse.ArgumentParser(description="M1-04 순차·병렬·실패 전파")
parser.add_argument("--case", default="pass", choices=[
    "pass", "false_success_claim", "missing_id", "missing_file", "wrong_request_id",
    "path_escape", "fake_summary", "missing_field", "offsetting_row_errors", "bad_request"])
parser.add_argument("--fault", default="none", choices=["none", "temporary", "persistent", "invalid"])
args = parser.parse_args()
result = run_case(args.case, args.fault)
print(json.dumps(result, ensure_ascii=False, indent=2))
