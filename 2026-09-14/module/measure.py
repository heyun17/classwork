import os
import csv
import time
import psutil
import re
from datetime import datetime

PROC = psutil.Process(os.getpid())

FIELDS = [
    "time", "target", "action", "lib", "width", "height",
    "mem_before_mb", "mem_after_mb", "mem_delta_mb",
    "cpu_pct", "elapsed_s"
]


def append_row(row, path="logs/resource_log.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    is_new = not os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)

        if is_new:
            writer.writeheader()

        writer.writerow(row)


def to_mb(v):
    return round(v / 1024**2, 1)


def measure(func, target="", action="", lib="", width="", height=""):
    PROC.cpu_percent(interval=None)

    before = to_mb(PROC.memory_info().rss)
    t0 = time.perf_counter()

    result = func()

    elapsed = time.perf_counter() - t0
    after = to_mb(PROC.memory_info().rss)
    cpu = PROC.cpu_percent(interval=None)

    row = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": target,
        "action": action,
        "lib": lib,
        "width": width,
        "height": height,
        "mem_before_mb": before,
        "mem_after_mb": after,
        "mem_delta_mb": round(after - before, 1),
        "cpu_pct": cpu,
        "elapsed_s": round(elapsed, 3),
    }

    return row, result
def parse_name(filename):
    m = re.search(r"(\d+)x(\d+)", filename)

    if m:
        return int(m.group(1)), int(m.group(2))

    return None, None

class ResourceLogger:
    def __init__(self, path="logs/resource_log.csv"):
        self.path = path
        self.rows = []
        self.proc = psutil.Process(os.getpid())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.save()
        return False

    def measure(self, func, **info):
        self.proc.cpu_percent(interval=None)

        before = to_mb(self.proc.memory_info().rss)
        t0 = time.perf_counter()

        result = func()

        elapsed = time.perf_counter() - t0
        after = to_mb(self.proc.memory_info().rss)

        row = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mem_before_mb": before,
            "mem_after_mb": after,
            "mem_delta_mb": round(after - before, 1),
            "cpu_pct": self.proc.cpu_percent(interval=None),
            "elapsed_s": round(elapsed, 3)
        }

        row.update(info)
        self.rows.append(row)

        return result

    def save(self):
        for r in self.rows:
            append_row(r, self.path)