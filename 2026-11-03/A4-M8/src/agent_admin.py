# ====================================================================
# A4-M8 · 사람이 쓰는 관리 명령 (Agent가 아니라 '사람'의 자리)
#   python src/agent_admin.py status     처리 이력(Memory)과 현재 버전
#   python src/agent_admin.py rollback   마지막 반영 되돌리기 (y/n 확인)
#   python src/agent_admin.py reset      실습 처음 상태로 (모든 반영 되돌리고 agent_state 삭제)
# ====================================================================
import shutil
import sys

import agent_tools as T


def status():
    st = T.load_state()
    print("버전:", st["version"], "| 마지막 평가:", st["last_eval"])
    for f, r in st["files"].items():
        print(f"  {r.get('status'):11} {f:34} {r.get('doc_id', '')}")
    for h in st["history"]:
        print(f"  v{h['version']} 반영: {h['doc_id']} ({h['dest']})")


def ask(file, reason):
    return "yes" if input(f"{reason}\n되돌릴까요? (y/n) ").strip().lower() in ("y", "yes") else "no"


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        status()
    elif cmd == "rollback":
        print(T.rollback_last(ask))
    elif cmd == "reset":
        while T.load_state()["history"]:
            print(T.rollback_last(lambda f, r: "yes"))
        shutil.rmtree(T.STATE_DIR, ignore_errors=True)
        print("agent_state 삭제 — 처음 상태입니다.")
