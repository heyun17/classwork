import pandas as pd

df = pd.read_csv("data/pokemon_100k.csv")

# 타입별 마릿수
print(df.groupby("type1").size())

# 타입별 평균 공격력
print(df.groupby("type1")["attack"].mean())

# 세대별 최대 체력
print(df.groupby("generation")["hp"].max())