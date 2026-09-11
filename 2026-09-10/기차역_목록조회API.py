"""국토교통부 TAGO 열차정보 API용 Python 예제.

기본값으로 제공된 공공데이터포털 인증키를 사용합니다.
다른 키를 사용하려면 환경변수 DATA_GO_KR_SERVICE_KEY를 설정하세요.
예: PowerShell에서 $env:DATA_GO_KR_SERVICE_KEY = '발급받은_키'
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen

API_BASE = "https://apis.data.go.kr/1613000/TrainInfo"
# 공공데이터포털에서 복사한 URL-encoded 인증키입니다.
# 환경변수 DATA_GO_KR_SERVICE_KEY가 있으면 환경변수 값이 우선됩니다.
DEFAULT_SERVICE_KEY = (
    "2%2BgpZJkXkLqLgJCJkzIaxN9%2Bp3f2q8EJ%2Brb8wunCLRjllJr5dy%2Bu4o09ZjyRxCXmnz%2B"
    "wheTgzgBIZKEV3%2B1Vkw%3D%3D"
)


def api_request(operation: str, **params: str | int) -> dict:
    # 포털에서 복사한 URL-encoded 키(%2B, %3D 등)도 그대로 붙여 넣을 수 있습니다.
    service_key = unquote(
        os.environ.get("DATA_GO_KR_SERVICE_KEY", DEFAULT_SERVICE_KEY).strip()
    )
    if not service_key:
        raise RuntimeError("공공데이터포털 인증키를 설정해 주세요.")

    query = {
        "serviceKey": service_key,
        "pageNo": params.pop("pageNo", 1),
        "numOfRows": params.pop("numOfRows", 100),
        "_type": "json",
        **params,
    }
    request = Request(
        f"{API_BASE}/{operation}?{urlencode(query)}",
        headers={"Accept": "application/json", "User-Agent": "TAGO-train-station-example/1.0"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    header = payload.get("response", {}).get("header", {})
    if str(header.get("resultCode", "00")) not in {"00", "0", "0000"}:
        raise RuntimeError(f"API 오류 {header.get('resultCode')}: {header.get('resultMsg')}")
    return payload.get("response", {}).get("body", {})


def items_from(body: dict) -> list[dict]:
    item = body.get("items", {}).get("item", [])
    return item if isinstance(item, list) else ([item] if item else [])


def get_city_codes() -> list[dict[str, str]]:
    body = api_request("GetCtyCodeList", pageNo=1, numOfRows=100)
    return [
        {"code": str(item.get("citycode", "")), "name": str(item.get("cityname", ""))}
        for item in items_from(body)
        if item.get("citycode") and item.get("cityname")
    ]


def get_stations_by_city(city: dict[str, str]) -> list[dict[str, str]]:
    body = api_request(
        "GetCtyAcctoTrainSttnList",
        cityCode=city["code"],
        pageNo=1,
        numOfRows=100,
    )
    stations = []
    for item in items_from(body):
        stations.append(
            {
                "city": city["name"],
                "name": str(item.get("nodename", "")),
                "code": str(item.get("nodeid", "")),
            }
        )
    return stations


def get_all_stations() -> list[dict[str, str]]:
    stations: list[dict[str, str]] = []
    for city in get_city_codes():
        print(f"조회 중: {city['name']} ({city['code']})", file=sys.stderr)
        stations.extend(get_stations_by_city(city))
    return sorted(stations, key=lambda item: (item["city"], item["name"]))


def main() -> None:
    stations = get_all_stations()
    output = Path("기차역_목록.csv")
    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["city", "name", "code"])
        writer.writeheader()
        writer.writerows(stations)
    print(f"완료: {len(stations):,}개 역을 {output.resolve()}에 저장했습니다.")


if __name__ == "__main__":
    main()
