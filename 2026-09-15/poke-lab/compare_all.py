import csv, gc
import pandas as pd
from collections import defaultdict
from measure import ResourceLogger

FILES = [
    ("data/pokemon_1k.csv", "1k"),
    ("data/pokemon_100k.csv", "100k"),
    ("data/pokemon_1m.csv", "1m"),
]

def by_csv_stream(path):
    """한 줄씩 읽으며 타입별 평균 공격력"""
    total, count = defaultdict(int), defaultdict(int)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = row["type1"]
            total[t] += int(row["attack"])
            count[t] += 1
    return {t: total[t]/count[t] for t in total}

def by_csv_list(path):
    """전부 리스트에 담은 뒤 계산"""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    total, count = defaultdict(int), defaultdict(int)
    for row in rows:
        total[row["type1"]] += int(row["attack"])
        count[row["type1"]] += 1
    return {t: total[t]/count[t] for t in total}

def by_pandas(path):
    """pandas 로 전체 읽고 집계"""
    d = pd.read_csv(path)
    return d.groupby("type1")["attack"].mean()

def by_pandas_opt(path):
    """필요한 열만, 형식 지정해서"""
    d = pd.read_csv(path, usecols=["type1", "attack"],
                    dtype={"type1": "category", "attack": "int16"})
    return d.groupby("type1", observed=True)["attack"].mean()

METHODS = [("csv-stream", by_csv_stream), ("csv-list", by_csv_list),
           ("pandas", by_pandas), ("pandas-opt", by_pandas_opt)]

with ResourceLogger() as logger:
    for path, label in FILES:
        for name, fn in METHODS:
            gc.collect()
            logger.measure(lambda: fn(path),
                           target=label, action="agg", lib=name)
            print(label, name, "완료")