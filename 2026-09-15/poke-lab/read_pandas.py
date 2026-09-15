import pandas as pd

df = pd.read_csv("data/pokemon_1k.csv", encoding="utf-8")

print(df.head())          # 앞 5줄
print(df.shape)           # (1000, 10)
print(df.columns.tolist())  # 열 이름 목록
print(df.info())          # 형식과 메모리
print(df.describe())      # 숫자 열 통계