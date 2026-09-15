import csv
from collections import defaultdict
from measure import ResourceLogger      # 앞 교재의 도구

path = "data/pokemon_100k.csv"

def count_stream():
    """한 줄씩 읽으며 세기 — 쌓지 않는다."""
    by_type = defaultdict(int)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_type[row["type1"]] += 1
    return by_type

def count_list():
    """전부 리스트에 담은 뒤 세기 — 쌓는다."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))     # ← 전부 메모리로
    by_type = defaultdict(int)
    for row in rows:
        by_type[row["type1"]] += 1
    return by_type

with ResourceLogger() as logger:
    logger.measure(count_stream, target="pokemon_100k",
                   action="count", lib="csv-stream")
    logger.measure(count_list, target="pokemon_100k",
                   action="count", lib="csv-list")