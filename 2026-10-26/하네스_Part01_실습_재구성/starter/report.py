"""Codex가 완성할 주문 보고서: 시작 파일에는 기능이 구현되어 있지 않다."""
from pathlib import Path

BASE = Path(__file__).resolve().parent

def make_report(source: Path, destination: Path, min_total: int = 0) -> int:
    """입력 CSV를 수정하지 않고, 주문 금액을 계산해 결과 CSV로 저장한다."""
    # 구현 과제: CSV 읽기, 수량·단가 검증, 중복 ID 검사, 필터 적용, 출력 저장
    raise NotImplementedError("Codex로 보고서 기능을 구현하세요")

if __name__ == "__main__":
    count = make_report(BASE / "orders.csv", BASE / "output" / "report.csv")
    print(f"보고서 {count}건 생성: output/report.csv")
