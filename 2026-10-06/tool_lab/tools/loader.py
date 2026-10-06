import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "sales.csv"


def load_rows(path: str | None = None) -> list[dict]:
    """CSV를 읽어 숫자 열을 변환한 뒤 리스트로 돌려준다."""
    target = Path(path) if path else DATA
    rows = []
    with open(target, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["quantity"] = int(row["quantity"])
            row["price"] = int(row["price"])
            row["amount"] = row["quantity"] * row["price"]
            # row["region"]+= str(row["amount"])
            rows.append(row)
    return rows

#from decimal import Decimal
#print(type(float(Decimal('10.5'))))
#print(float(Decimal('10.5')))
#from datetime import datetime
#import json
#json.dumps({"now": datetime.now()})
#a=datetime.now().isoformat()
#a=str(datetime.now())
#print(f'type: {type(a)} \n {a}')

print(load_rows.__annotations__)