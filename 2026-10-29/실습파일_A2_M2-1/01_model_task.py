"""Hugging Face Hub에 올라온 사전학습 모델의 설정(config)과 토크나이저를 불러와
이 모델이 어떤 Task(예: 문장 분류)용인지, 입력을 어떻게 처리하는지 확인한다.
모델 가중치는 내려받지 않으므로 가볍게 실행된다.
"""
from transformers import AutoConfig, AutoTokenizer

# Hub 모델 ID: "작성자/모델이름" 형식
# KR-FinBert-SC: 한국어 금융 문장 감성 분류(Sentiment Classification) 모델
name = "snunlp/KR-FinBert-SC"

# AutoConfig: 모델 구조·라벨 정보가 담긴 config.json만 불러온다 (가중치 X)
config = AutoConfig.from_pretrained(name)
# AutoTokenizer: 모델에 맞는 토크나이저 클래스를 자동으로 골라 불러온다
tok = AutoTokenizer.from_pretrained(name)

print("모델:", name)

# model_type: 기반 아키텍처 (bert, roberta, gpt2 등)
print("model_type:", config.model_type)

# num_labels / id2label / label2id: 분류 모델이면 출력 클래스 정보가 들어 있다
# - 라벨이 여러 개 → 분류(Sequence/Token Classification) Task 모델임을 알 수 있음
# - id2label: 모델 출력 인덱스 → 사람이 읽는 라벨 이름 (예측 결과 해석에 사용)
# - label2id: 라벨 이름 → 인덱스 (학습 데이터 라벨을 숫자로 바꿀 때 사용)
print("num_labels:", config.num_labels)
print("id2label:", config.id2label)
print("label2id:", config.label2id)

# 토크나이저 종류: 문장을 어떤 방식(WordPiece, BPE 등)으로 쪼개는지 결정
print("tokenizer:", type(tok).__name__)

# vocab_size: 토크나이저가 아는 토큰(단어 조각) 개수
print("vocab_size:", tok.vocab_size)

# 입력 최대 길이(토큰 수): 이보다 긴 문장은 잘라서(truncation) 넣어야 한다
# tokenizer 설정에 최대 길이가 없으면 매우 큰 값(약 1e30)이 들어가므로
# 그때는 모델이 실제로 처리할 수 있는 위치 임베딩 개수(max_position_embeddings)를 사용
max_len = tok.model_max_length if tok.model_max_length < 100_000 else config.max_position_embeddings
print("입력 최대 길이:", max_len)

print("이 정보는 어떤 Task의 모델인지 판단할 때 필요합니다.")
