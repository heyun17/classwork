"""Codex로 A/B 비교하기 위한 두 동일한 시작 폴더를 만든다."""
from pathlib import Path
from shutil import copy2, rmtree

BASE = Path(__file__).resolve().parent

def prepare():
    for kind in ("without_harness", "with_harness"):
        target = BASE / "experiments" / kind
        if target.exists(): rmtree(target)
        target.mkdir(parents=True)
        for name in ("orders.csv", "orders.sha256", "report.py", "test_report.py"):
            copy2(BASE / "starter" / name, target / name)
        if kind == "with_harness":
            copy2(BASE / "contracts" / "AGENTS.md", target / "AGENTS.md")
        print(f"준비됨: {target.relative_to(BASE)}")

if __name__ == "__main__": prepare()
