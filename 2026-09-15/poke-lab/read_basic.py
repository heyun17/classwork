import csv

path = "data/pokemon_1k.csv"

with open(path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    print("열 이름:", reader.fieldnames)

    for i, row in enumerate(reader):
        if i >= 3:                     # 앞 3줄만 보고 멈춤
            break
        print(row)