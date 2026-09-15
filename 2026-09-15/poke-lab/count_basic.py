import csv
from collections import defaultdict

path = "data/pokemon_100k.csv"

total = 0
legendary = 0
by_type = defaultdict(int)        # 없는 키는 0으로 시작

with open(path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        total += 1
        if row["legendary"] == "1":        # 문자열로 비교
            legendary += 1
        by_type[row["type1"]] += 1

print("전체", total)
print("전설", legendary, f"({legendary/total*100:.1f}%)")

# 많은 순으로 정렬해서 출력
for t, c in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
    print(f"{t:6} {c:6,}")