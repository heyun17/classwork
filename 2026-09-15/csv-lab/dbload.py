"""sales_100k.db를 읽어 판매 데이터의 기본 통계를 출력한다.

이 프로그램은 Python 표준 라이브러리인 sqlite3만 사용한다.
데이터베이스 경로는 현재 작업 폴더가 아니라 이 파일의 위치를 기준으로
계산하므로, 어느 폴더에서 실행해도 같은 DB를 읽을 수 있다.
"""

from pathlib import Path
import sqlite3
import time


# dbload.py가 있는 폴더를 기준으로 경로를 계산한다.
# 상대 경로를 현재 터미널 위치 기준으로 만들면 실행 위치에 따라
# 파일을 못 찾을 수 있으므로, 항상 이 파일 옆의 data 폴더를 사용한다.
DB_PATH = Path(__file__).resolve().parent / "data" / "sales_100k.db"


def open_database() -> sqlite3.Connection:
    """SQLite DB를 읽기 전용으로 연다.

    SQLite 파일은 첫 16바이트가 'SQLite format 3' 식별자로 시작한다.
    이 검사를 먼저 하면 CSV의 확장자만 .db로 바꾼 파일을 잘못 읽는
    문제를 쉽게 발견할 수 있다. query_only 설정으로 원본 DB를
    분석 중 수정하지 않는다.
    """

    if not DB_PATH.is_file():
        raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다: {DB_PATH}")

    with DB_PATH.open("rb") as file:
        if file.read(16) != b"SQLite format 3\x00":
            raise ValueError(
                "sales_100k.db가 SQLite 형식이 아닙니다. "
                "CSV의 확장자만 변경한 파일인지 확인하세요."
            )

    # Windows 경로에 # 같은 문자가 있어도 안전하게 처리되도록 일반 경로로
    # 연결한다. 파일 존재 여부는 위에서 확인했고, 아래 query_only 설정으로
    # 이 연결에서는 INSERT/UPDATE 같은 변경 작업을 허용하지 않는다.
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def main() -> None:
    """DB를 연결하고 요구된 네 가지 통계를 순서대로 출력한다."""

    started_at = time.perf_counter()

    with open_database() as connection:
        # 이번 실습에서 만든 테이블 이름은 sales이다.
        # COUNT(*)는 특정 컬럼이 NULL이어도 행 전체를 세므로 전체 건수에 적합하다.
        total_count = connection.execute(
            "SELECT COUNT(*) AS count FROM sales"
        ).fetchone()["count"]

        print(f"데이터베이스: {DB_PATH}")
        print("테이블: sales")
        print(f"전체 건수: {total_count:,}")
        print()

        # region별 건수를 GROUP BY로 묶는다.
        # 전체 건수가 0일 때 0으로 나누지 않도록 비율을 별도로 처리한다.
        print("[region별 건수 및 비율]")
        print(f"{'region':<12}{'건수':>15}{'비율(%)':>12}")
        print("-" * 39)
        region_rows = connection.execute(
            """
            SELECT region, COUNT(*) AS count
            FROM sales
            GROUP BY region
            ORDER BY count DESC, region
            """
        )
        for row in region_rows:
            region = "(NULL)" if row["region"] is None else str(row["region"])
            count = row["count"]
            ratio = count / total_count * 100 if total_count else 0
            print(f"{region:<12}{count:>15,}{ratio:>11.2f}")
        print()

        # SUM(qty)는 수량 합계, AVG(qty)는 수량 평균이다.
        # 데이터가 비어 있으면 SQL 결과가 NULL이므로 출력 전에 0으로 바꾼다.
        qty_row = connection.execute(
            "SELECT SUM(qty) AS total_qty, AVG(qty) AS average_qty FROM sales"
        ).fetchone()
        total_qty = 0 if qty_row["total_qty"] is None else qty_row["total_qty"]
        average_qty = (
            0.0 if qty_row["average_qty"] is None else qty_row["average_qty"]
        )
        print("[qty 통계]")
        print(f"합계: {total_qty:,}")
        print(f"평균: {average_qty:,.2f}")
        print()

        # 날짜가 YYYY-MM-DD 형식이므로 substr(date, 1, 7)로 YYYY-MM을 만든다.
        # 만든 년월을 GROUP BY하여 각 월의 판매금액(amount)을 합산한다.
        print("[년월별 판매금액 합계]")
        print(f"{'년월':<12}{'판매금액 합계':>20}")
        print("-" * 32)
        month_rows = connection.execute(
            """
            SELECT substr(date, 1, 7) AS year_month, SUM(amount) AS total_amount
            FROM sales
            GROUP BY substr(date, 1, 7)
            ORDER BY year_month
            """
        )
        for row in month_rows:
            year_month = "(NULL)" if row["year_month"] is None else row["year_month"]
            total_amount = 0 if row["total_amount"] is None else row["total_amount"]
            print(f"{year_month:<12}{total_amount:>20,}")

    elapsed = time.perf_counter() - started_at
    print()
    print(f"처리 시간: {elapsed:.3f}초")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, sqlite3.DatabaseError) as error:
        print(f"오류: {error}")
        raise SystemExit(1)
