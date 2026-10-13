import json
from datetime import datetime

from config import DATA_DIR


HISTORY_FILE = DATA_DIR / "history.jsonl"


def save_history(rooms: list[dict]) -> None:
    """검증을 통과한 분석 결과를 JSONL로 누적 저장한다."""
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rooms": rooms,
    }

    with HISTORY_FILE.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )


def get_recent_history(limit: int = 3) -> list[dict]:
    """최근 분석 기록을 가져온다."""
    if not HISTORY_FILE.exists():
        return []

    lines = HISTORY_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    return [
        json.loads(line)
        for line in lines[-limit:]
        if line.strip()
    ]
