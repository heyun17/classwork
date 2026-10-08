import pandas as pd

data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'score': [80, 95, 70]
}

df = pd.DataFrame(data)

print(df[df['score'] >= 80])