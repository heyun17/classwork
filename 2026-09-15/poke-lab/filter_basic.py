import pandas as pd

df = pd.read_csv("data/pokemon_100k.csv")

# 전설 포켓몬만
legend = df[df["legendary"] == 1]
print(len(legend))

# 불꽃 타입만
fire = df[df["type1"] == "불꽃"]

# 공격력 150 이상
strong = df[df["attack"] >= 150]

print(len(legend), len(fire), len(strong))