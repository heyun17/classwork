import pandas as pd
import os

df = pd.read_csv("data/pokemon_1m.csv")

summary = df.groupby("type1").agg(
    count=("id", "count"),
    avg_attack=("attack", "mean"),
    max_hp=("hp", "max"),
).round(1).reset_index()      # 묶음 기준을 열로 되돌림

os.makedirs("output", exist_ok=True)

summary.to_csv("output/summary.csv",
              index=False, encoding="utf-8-sig")
summary.to_json("output/summary.json",
               orient="records", force_ascii=False, indent=2)

for name in ("summary.csv", "summary.json"):
    size = os.path.getsize(f"output/{name}")
    print(f"{name:16} {size:,} 바이트")