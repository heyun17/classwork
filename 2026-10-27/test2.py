from kiwipiepy import Kiwi
import pandas as pd
kiwi = Kiwi()

texts = [
    "배달이 너무 늦어요",
    "음식이 정말 맛있어요",
    "결제가 계속 실패해요"
]

rows = []
for text in texts:
    nouns = []
    for t in kiwi.tokenize(text):
        if t.tag in ("NNG", "NNP"):
            nouns.append(t.form)
    rows.append([text, ";".join(nouns)])

df = pd.DataFrame(rows, columns=["VOC_원문", "명사_대상"])
print(df.to_string(index=False))