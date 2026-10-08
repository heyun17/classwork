import csv
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "sales.csv"

mcp = MCPServer("sales")

Region = Literal["서울", "부산", "대구"]


class Sale(BaseModel):
    region: str
    amount: int = Field(ge=0, description="금액(만원)")


def load_sales() -> list[Sale]:
    with CSV_PATH.open(encoding="utf-8") as f:
        return [Sale(region=row["지역"], amount=int(row["금액"])) for row in csv.DictReader(f)]


@mcp.tool()
def region_total(region: Region) -> int:
    """한 지역의 매출 합계(만원)를 돌려준다."""
    return sum(s.amount for s in load_sales() if s.region == region)


@mcp.tool()
def top_regions(
    n: Annotated[int, Field(description="상위 몇 개 지역을 볼지", ge=1, le=3)] = 1,
) -> dict[str, int]:
    """매출 합계가 큰 지역부터 n개를 돌려준다."""
    totals: dict[str, int] = {}
    for s in load_sales():
        totals[s.region] = totals.get(s.region, 0) + s.amount
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return dict(ranked[:n])


@mcp.tool()
def add_sale(sale: Sale) -> int:
    """매출 한 건을 sales.csv에 추가하고 전체 건수를 돌려준다."""
    if sale.region not in ("서울", "부산", "대구"):
        raise ToolError(f"등록되지 않은 지역입니다: {sale.region}")
    with CSV_PATH.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([sale.region, sale.amount])
    return len(load_sales())


@mcp.tool()
def broken() -> str:
    """일반 예외가 어떻게 보이는지 확인하는 도구."""
    raise ValueError("DB 비밀번호가 틀렸습니다: pw=1234")


@mcp.resource("sales://csv")
def sales_csv() -> str:
    """sales.csv 원본."""
    return CSV_PATH.read_text(encoding="utf-8")


@mcp.resource("sales://region/{region}")
def region_rows(region: str) -> str:
    """한 지역의 매출 행만 CSV 형식으로 돌려준다."""
    rows = [f"{s.region},{s.amount}" for s in load_sales() if s.region == region]
    return "\n".join(rows)


@mcp.prompt()
def sales_report(region: str, tone: str = "간결하게") -> str:
    """지역 매출 보고서 작성 지시문."""
    return (
        f"sales 서버의 region_total 도구로 {region} 매출을 조회하고, "
        f"{tone} 3줄 보고서를 작성해 줘."
    )

if __name__ == "__main__":
    mcp.run()