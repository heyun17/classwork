import pandas as pd

df = pd.read_csv("data/pokemon_100k.csv")

# 전체 / 전설
print(len(df))
print(df["legendary"].sum())          # 1의 합 = 전설 마릿수

# 타입별 마릿수 — 이 한 줄
print(df["type1"].value_counts())

# 빈 값 확인
print(df["type2"].isna().sum(), "마리는 두 번째 타입 없음")