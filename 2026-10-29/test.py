from transformers import pipeline

model = pipeline(
    "text-classification",
    model="snunlp/KR-FinBert-SC"
)

print(model("삼성전자의 영업이익이 크게 증가했다."))