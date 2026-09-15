import csv
import gc
import json
from pathlib import Path

import pandas as pd

from measure import ResourceLogger


BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "static" / "data.csv"
JSON_PATH = BASE_DIR / "static" / "data.json"
LOG_PATH = BASE_DIR / "logs" / "resource_log.csv"


def read_with_csv():
    """csv 모듈로 CSV를 읽습니다."""
    with CSV_PATH.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_with_json():
    """json 모듈로 JSON을 읽습니다."""
    with JSON_PATH.open(encoding="utf-8") as file:
        return json.load(file)


readers = [
    ("data.csv", "csv", read_with_csv),
    ("data.json", "json", read_with_json),
    ("data.csv", "pandas_csv", lambda: pd.read_csv(CSV_PATH)),
    ("data.json", "pandas_json", lambda: pd.read_json(JSON_PATH)),
]

for target, lib, reader in readers:
    file_path = BASE_DIR / "static" / target
    file_size = file_path.stat().st_size

    for _ in range(5):
        # 측정 결과를 변수에만 담고, 다음 측정 전에 삭제합니다.
        with ResourceLogger(LOG_PATH) as logger:
            data = logger.measure(
                reader,
                target=target,
                action="read",
                lib=lib,
            )
            logger.rows[-1].update(rows=len(data), file_size=file_size)

        del data
        gc.collect()
