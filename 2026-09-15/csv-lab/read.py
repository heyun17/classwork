import csv

with open("data\sales_1k.csv", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)          # 첫 줄을 꺼내 헤더로
    for row in reader:
        print(row[0], row[3])     # 리스트 → 위치로 꺼냄

# row = ['2026-09-01', '서울', '노트북', '1250000']