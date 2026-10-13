from memory import get_recent_history, save_history
from validator import validate_batch
from yolo_service import MeetingRoomDetector


_detector: MeetingRoomDetector | None = None


def get_detector() -> MeetingRoomDetector:
    """YOLO 모델을 필요할 때 한 번만 로드한다."""
    global _detector

    if _detector is None:
        _detector = MeetingRoomDetector()

    return _detector


def analyze_all_rooms() -> dict:
    """모든 회의실 이미지를 YOLO로 분석하고 결과를 검증한다."""
    try:
        rooms = get_detector().analyze_all()

        errors = validate_batch(rooms)

        if errors:
            return {
                "ok": False,
                "error": "검증 실패",
                "details": errors,
            }

        save_history(rooms)

        return {
            "ok": True,
            "rooms": rooms,
        }

    except Exception as error:
        return {
            "ok": False,
            "error": str(error),
        }


def recent_history(limit: int = 3) -> dict:
    """최근 분석 이력을 조회한다."""
    limit = max(1, min(limit, 10))

    return {
        "ok": True,
        "history": get_recent_history(limit),
    }


TOOLS = [
    {
        "type": "function",
        "name": "analyze_all_rooms",
        "description": (
            "meeting_rooms 폴더의 모든 회의실 이미지를 YOLO로 분석한다. "
            "사람 수, 상태, 탐지 객체와 Bounding Box 결과 이미지 경로를 반환한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "recent_history",
        "description": (
            "과거 회의실 분석 기록을 조회한다. "
            "현재 상태가 아니라 이전 상태와 비교할 때만 사용한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                }
            },
            "additionalProperties": False,
        },
    },
]
