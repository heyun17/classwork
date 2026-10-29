"""교안 02: AutoModel·AutoTokenizer·pipeline으로 문장을 분류하고 라벨별 점수를 확인한다.
01에서는 config만 봤다면, 여기서는 모델 가중치까지 내려받아 실제로 예측을 해 본다.
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Hub 모델 ID: 한국어 금융 문장 감성 분류 모델 (negative / neutral / positive)
name = "snunlp/KR-FinBert-SC"

# AutoTokenizer: 문장 → 토큰 ID로 바꿔 주는 토크나이저
tok = AutoTokenizer.from_pretrained(name)
# AutoModelForSequenceClassification: 문장 분류용 헤드(출력층)가 붙은 모델
# - 가중치(pytorch_model.bin / model.safetensors)까지 내려받는다
# - 모델 config도 함께 로드되므로 model.config로 라벨 정보를 볼 수 있다
model = AutoModelForSequenceClassification.from_pretrained(name)

# id2label: 모델 출력 인덱스 → 라벨 이름 (예측 결과를 사람이 읽을 수 있게 해 줌)
print("config.id2label:", model.config.id2label)
# num_labels: 분류할 클래스 개수 = 모델 출력(logits) 차원 수
print("config.num_labels:", model.config.num_labels)

# pipeline: 토큰화 → 모델 추론 → 후처리(softmax, 라벨 이름 붙이기)를 한 번에 해 주는 도구
# - "text-classification": 문장 분류 Task
# - model / tokenizer: 위에서 불러온 객체를 그대로 넘겨 재사용 (다시 다운로드하지 않음)
# - device=-1: CPU 사용 (GPU가 있으면 0, 1, ... 처럼 GPU 번호 지정)
classifier = pipeline("text-classification", model=model, tokenizer=tok, device=-1)

# 분류해 볼 예시 문장: 긍정적인 문장 1개, 부정적인 문장 1개
texts = ["기업 실적이 크게 개선되었다.", "기업의 주가가 크게 하락했다."]

# 기본 호출: 문장마다 점수가 가장 높은 라벨 1개만 돌려준다
# 결과 형태: [{'label': ..., 'score': ...}, ...]  (문장 수만큼)
print("\n[가장 높은 분류]")
for text, pred in zip(texts, classifier(texts)):
    print(f"  {text} → {pred['label']} ({pred['score']:.4f})")

# top_k=None: 모든 라벨의 점수를 높은 순으로 돌려준다
# - score는 softmax 확률이므로 한 문장의 라벨 점수를 모두 더하면 1이 된다
# - 1등과 2등 점수 차이를 보면 모델이 얼마나 확신하는지 알 수 있다
print("\n[모든 라벨별 점수]")
for text, preds in zip(texts, classifier(texts, top_k=None)):
    print(f"  {text}")
    for p in preds:
        print(f"    {p['label']:<8} {p['score']:.4f}")
