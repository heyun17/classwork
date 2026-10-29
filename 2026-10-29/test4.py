
from transformers import pipeline

model = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
)

text = "devops나 시스템 엔지니어가 가장 필요로 하는 과정은?"
labels = ["ai", "클라우드", "컨텐츠 크리에이트", "데이터 분석"]

result = model(text, candidate_labels=labels)

for label, score in zip(result["labels"], result["scores"]):
    print(label, round(score * 100, 2), "%")
