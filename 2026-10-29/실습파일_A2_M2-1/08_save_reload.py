"""교안 08: 모델 + 토크나이저 save_pretrained 후 로컬 재로딩.
Hub에서 받은 모델을 로컬 폴더에 저장하고, 인터넷 없이 그 폴더에서 다시 불러와 예측해 본다.
파인튜닝한 모델(07의 saved_model_07)도 같은 방법으로 불러올 수 있다.
"""
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Hub 모델 ID: 한국어 금융 문장 감성 분류 모델
name = "snunlp/KR-FinBert-SC"
# 저장할 로컬 폴더 (없으면 save_pretrained가 만들어 준다)
folder = Path("saved_model_08")

# 1) Hub에서 모델과 토크나이저 불러오기
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForSequenceClassification.from_pretrained(name)

# 2) 로컬 폴더에 저장
# - 모델: config.json(구조·라벨 정보) + model.safetensors(가중치)
# - 토크나이저: tokenizer.json(단어 사전·규칙) + tokenizer_config.json(설정)
# - 모델과 토크나이저는 반드시 짝을 맞춰 같은 폴더에 저장해야 한다
#   (토크나이저가 다르면 같은 문장이 다른 토큰 ID로 바뀌어 예측이 엉망이 됨)
model.save_pretrained(folder)
tok.save_pretrained(folder)
print("저장된 파일:", sorted(p.name for p in folder.iterdir()))

# 3) 로컬 폴더에서 다시 불러오기
# - from_pretrained에 Hub ID 대신 폴더 경로를 주면 로컬에서 불러온다
# - local_files_only=True: 인터넷에 접속하지 않고 로컬 파일만 사용
#   (폐쇄망·오프라인 환경이나 네트워크 오류가 날 때 유용)
local_tok = AutoTokenizer.from_pretrained(folder, local_files_only=True)
local_model = AutoModelForSequenceClassification.from_pretrained(folder, local_files_only=True)

# config.json에 저장된 라벨 정보가 그대로 복원되었는지 확인
print("라벨:", local_model.config.id2label)

# 4) 다시 불러온 모델로 예측
# 원본 모델과 같은 결과가 나오면 저장·재로딩이 제대로 된 것이다
clf = pipeline("text-classification", model=local_model, tokenizer=local_tok, device=-1)
print("로컬 예측:", clf("기업 실적이 증가했습니다."))
