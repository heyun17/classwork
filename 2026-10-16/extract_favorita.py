from pathlib import Path
import zipfile
import py7zr

BASE = Path("06_favorita")

ZIP_PATH = BASE / "favorita-grocery-sales-forecasting.zip"
TEMP = BASE / "_packed"

NEEDED = [
    "train.csv.7z",
    "items.csv.7z",
    "stores.csv.7z",
    "transactions.csv.7z",
    "holidays_events.csv.7z",
    "oil.csv.7z",
]

TEMP.mkdir(exist_ok=True)

# 1. 바깥 ZIP에서 필요한 7z만 추출
print("[1/2] 필요한 7z 파일 추출")

with zipfile.ZipFile(ZIP_PATH, "r") as z:
    for name in NEEDED:
        print("  ", name)
        z.extract(name, TEMP)

# 2. 각 7z → CSV
print("\n[2/2] 7z 압축 해제")

for name in NEEDED:
    archive = TEMP / name

    print("  ", name)

    with py7zr.SevenZipFile(archive, mode="r") as z:
        z.extractall(path=BASE)

print("\n완료")