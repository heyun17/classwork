from config import SMALL_GROUP_MAX


def expected_state(person_count: int) -> str:
    if person_count == 0:
        return "비어있음"

    if person_count <= SMALL_GROUP_MAX:
        return "소규모"

    return "혼잡"


def validate_room(room: dict) -> list[str]:
    """YOLO/Python 처리 결과가 내부 규칙과 일치하는지 검증한다."""
    errors: list[str] = []

    count = room.get("person_count")
    state = room.get("state")

    if not isinstance(count, int):
        errors.append("person_count가 정수가 아닙니다.")
        return errors

    if count < 0:
        errors.append("person_count가 음수입니다.")

    correct_state = expected_state(count)

    if state != correct_state:
        errors.append(
            f"상태 불일치: {count}명인데 {state}로 분류됨"
        )

    return errors


def validate_batch(rooms: list[dict]) -> list[str]:
    errors: list[str] = []

    for room in rooms:
        for error in validate_room(room):
            errors.append(f"{room.get('file')}: {error}")

    return errors
