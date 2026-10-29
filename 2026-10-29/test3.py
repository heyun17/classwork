
from transformers import pipeline

# 모델 불러오기 (최초 실행 시 자동 다운로드)
model = pipeline(
    "text-classification",
    model="joonhyun-kim/roberta-base-klue-ynat-classification"
)

# 뉴스 제목 입력
text = input("뉴스 제목: ")

# 분류
result = model(text)[0]

print("분류:", result["label"])
print("확률:", round(result["score"] * 100, 2), "%")
