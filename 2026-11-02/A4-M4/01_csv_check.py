# ====================================================================
# 파일 용도: 제공된 CSV 데이터의 행 수, 컬럼, 샘플 레코드를 확인합니다.
# ====================================================================

import pandas as pd

from config import CSV_PATH

df = pd.read_csv(
    CSV_PATH
)

print("CSV 행 수:", len(df))
print("\n앞 5행:")
print(df.head())

print("\n첫 번째 행을 dict로 보기:")
records = df.to_dict(
    orient="records"
)
print(records[0])
