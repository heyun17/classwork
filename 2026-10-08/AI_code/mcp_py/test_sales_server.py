import shutil
from pathlib import Path

import pytest
from mcp import Client

import sales_server
from sales_server import mcp


@pytest.fixture
def csv_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "sales.csv"
    shutil.copy(sales_server.CSV_PATH, target)
    monkeypatch.setattr(sales_server, "CSV_PATH", target)
    return target


@pytest.mark.anyio
async def test_region_total(csv_copy: Path) -> None:
    async with Client(mcp) as client:
        r = await client.call_tool("region_total", {"region": "서울"})
    assert r.structured_content == {"result": 150}


@pytest.mark.anyio
async def test_unknown_region_rejected(csv_copy: Path) -> None:
    async with Client(mcp) as client:
        r = await client.call_tool("region_total", {"region": "광주"})
    assert r.is_error


@pytest.mark.anyio
async def test_add_sale_writes_copy_only(csv_copy: Path) -> None:
    before = len(sales_server.load_sales())
    async with Client(mcp) as client:
        r = await client.call_tool("add_sale", {"sale": {"region": "대구", "amount": 5}})
    assert r.structured_content == {"result": before + 1}
    assert csv_copy.read_text(encoding="utf-8").strip().endswith("대구,5")