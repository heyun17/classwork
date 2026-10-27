"""스킬이 호출하는 결정적 검증 스크립트."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
print("[Skill] 검사 프로젝트:",ROOT, flush=True)
result = subprocess.run(cmd, cwd=ROOT, check=False)
raise SystemExit(result.returncode)
