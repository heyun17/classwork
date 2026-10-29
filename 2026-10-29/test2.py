from transformers import pipeline

model = pipeline("text-classification", model="snunlp/KR-FinBert-SC")

labels = {"negative": 0, "neutral": 1, "positive": 2}

text = input("문장 입력: ")
result = model(text)[0]

print("라벨:", labels[result["label"]])
print("확신도:", round(result["score"], 4))
