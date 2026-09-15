import time, requests
from measure import ResourceLogger
from extract import extract

def fetch_many(n=50):
    rows, total_bytes = [], 0
    for i in range(1, n + 1):
        url = f"https://pokeapi.co/api/v2/pokemon/{i}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            total_bytes += len(res.content)
            rows.append(extract(res.json()))
        time.sleep(0.1)              # 서버 배려 — 아래 설명
    print(f"전송량 {total_bytes/1024/1024:.1f} MB")
    return rows

with ResourceLogger() as logger:
    rows = logger.measure(lambda: fetch_many(50),
                          target="pokeapi", action="fetch", lib="requests-50")
print(len(rows), "마리")
