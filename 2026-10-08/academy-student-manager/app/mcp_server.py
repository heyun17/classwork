from mcp.server import MCPServer

from app.database import SessionLocal
from app.schemas import StudentDetailResponse
from app.services import (
    get_dashboard_summary,
    get_student_detail as get_student_detail_service,
)


mcp = MCPServer("Academy Student Manager")


@mcp.tool()
def get_dashboard() -> dict[str, int]:
    """학원의 학생 수, 오늘 출결, 이번 달 수납 현황을 조회한다."""
    with SessionLocal() as session:
        return get_dashboard_summary(session)


@mcp.tool()
def get_student_detail(student_id: int) -> dict[str, object]:
    """학생 ID로 학생 기본정보, 최근 출결, 이번 달 수납 정보를 조회한다."""
    with SessionLocal() as session:
        try:
            result = get_student_detail_service(
                session=session,
                student_id=student_id,
            )
        except LookupError as error:
            return {
                "error": str(error),
            }

        response = StudentDetailResponse.model_validate(result)

        return response.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
    )