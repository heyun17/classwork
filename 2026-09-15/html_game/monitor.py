import csv
import os
import time
from datetime import datetime

import psutil

log_file = "resource_log.csv"
write_header = not os.path.exists(log_file) or os.path.getsize(log_file) == 0
prev_net = psutil.net_io_counters()

try:
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if write_header:
            writer.writerow([
                "datetime",
                "cpu_percent",
                "memory_percent",
                "memory_used_mb",
                "bytes_sent_total",
                "bytes_recv_total",
                "bytes_sent_1sec",
                "bytes_recv_1sec",
            ])
            f.flush()

        while True:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            net = psutil.net_io_counters()
            now = datetime.now()

            sent_1sec = net.bytes_sent - prev_net.bytes_sent
            recv_1sec = net.bytes_recv - prev_net.bytes_recv
            prev_net = net

            writer.writerow([
                now.strftime("%Y-%m-%d %H:%M:%S"),
                cpu,
                memory.percent,
                round(memory.used / 1024 / 1024, 1),
                net.bytes_sent,
                net.bytes_recv,
                sent_1sec,
                recv_1sec,
            ])
            f.flush()

            print(
                f"{now:%H:%M:%S} | CPU {cpu:.1f}% | RAM {memory.percent:.1f}% | "
                f"SEND {sent_1sec} B/s | RECV {recv_1sec} B/s"
            )

except KeyboardInterrupt:
    print("\n모니터링을 종료했습니다.")
