"""교안 07: 제조품질 3분류 Trainer 실습. CPU에는 시간이 걸림. 시험용 소규모 데이터.
사전학습된 klue/bert-base에 분류 헤드를 붙이고, 제조 품질 문장(불량/정상/경미한 불량)으로
파인튜닝(추가 학습)한 뒤 독립 테스트 데이터로 평가하고 모델을 저장한다.
같은 폴더에 manufacturing_sample.csv(text, label 컬럼)가 있어야 한다.
"""
import csv
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from datasets import Dataset
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          DataCollatorWithPadding, Trainer, TrainingArguments, set_seed)

# set_seed: 무작위 값을 고정해 실행할 때마다 같은 결과가 나오게 한다
# - 새로 붙는 분류 헤드는 모델을 불러올 때 무작위로 초기화되므로,
#   TrainingArguments의 seed만으로는 부족하고 모델 로드 전에 고정해야 한다
set_seed(42)

# 1) CSV 읽기
# - encoding="utf-8-sig": 엑셀에서 저장한 CSV 맨 앞의 BOM 문자를 자동으로 제거
# - csv.DictReader: 각 행을 {"text": ..., "label": ...} 형태의 dict로 읽는다
source = Path(__file__).with_name("manufacturing_sample.csv")
with source.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
labels = [int(r["label"]) for r in rows]
index = list(range(len(rows)))

# 2) train / valid / test 3개로 나누기 (60% / 20% / 20%)
# - train: 학습에 사용, valid: 학습 중 성능 확인, test: 학습이 끝난 뒤 한 번만 평가
# - stratify=labels: 나눈 각 데이터에 라벨 비율이 원본과 같게 유지되도록 한다
#   (데이터가 적을 때 한쪽에 특정 라벨이 몰리는 것을 막음)
# - random_state=42: 나누는 결과를 고정
train_idx, other_idx = train_test_split(index, test_size=0.4, random_state=42, stratify=labels)
valid_idx, test_idx = train_test_split(other_idx, test_size=0.5, random_state=42,
                                       stratify=[labels[i] for i in other_idx])

def as_data(ids):
    # 인덱스 목록 → Hugging Face Dataset
    # Trainer는 정답 컬럼 이름을 "labels"로 기대하므로 이름을 맞춰 준다
    return Dataset.from_dict({"text": [rows[i]["text"] for i in ids],
                              "labels": [int(rows[i]["label"]) for i in ids]})

# 3) 토큰화
name = "klue/bert-base"
tok = AutoTokenizer.from_pretrained(name)

def preprocess(batch):
    # 96토큰보다 긴 문장은 잘라낸다. 패딩은 아래 DataCollator가 배치마다 처리
    return tok(batch["text"], truncation=True, max_length=96)

train_ds = as_data(train_idx).map(preprocess, batched=True)
valid_ds = as_data(valid_idx).map(preprocess, batched=True)
test_ds = as_data(test_idx).map(preprocess, batched=True)

# 4) 모델 준비
# - klue/bert-base는 분류용으로 학습된 모델이 아니므로 분류 헤드(classifier)가 없다
# - num_labels=3을 주면 3개 클래스를 출력하는 분류 헤드를 새로 붙인다 (값은 무작위로 시작)
#   → 실행 시 나오는 MISSING(classifier.weight/bias) 메시지는 이 새 헤드를 뜻하므로 정상
#   → UNEXPECTED(cls.predictions...)는 사전학습용 헤드라 분류에서는 버려지는 것이므로 무시해도 된다
# - id2label / label2id를 함께 저장해 두면 예측 결과를 라벨 이름으로 볼 수 있다
labels_dict = {0: "불량", 1: "정상", 2: "경미한 불량"}
model = AutoModelForSequenceClassification.from_pretrained(
    name, num_labels=3, id2label=labels_dict,
    label2id={v: k for k, v in labels_dict.items()})

def metrics(p):
    # 평가 지표 계산 함수: Trainer가 평가할 때마다 호출한다
    # - p.predictions: 모델 출력 점수(logits), [샘플 수, 3]
    # - argmax: 점수가 가장 높은 클래스 번호를 예측값으로 사용
    # - f1 average="macro": 클래스별 F1을 단순 평균 (라벨마다 똑같은 비중으로 평가)
    pred = np.argmax(p.predictions, axis=-1)
    return {"accuracy": accuracy_score(p.label_ids, pred),
            "f1": f1_score(p.label_ids, pred, average="macro", zero_division=0)}

# 5) 학습 설정
# - output_dir: 체크포인트(중간 저장 모델)를 저장할 폴더
# - num_train_epochs=1: 학습 데이터를 1번만 훑는다 (실습용으로 짧게)
# - per_device_*_batch_size=4: 한 번에 4문장씩 학습/평가
# - eval_strategy / save_strategy="epoch": 에폭이 끝날 때마다 valid 평가와 저장
# - report_to="none": wandb 같은 외부 기록 도구를 쓰지 않음
# - seed=42: 가중치 초기화·데이터 섞기 순서를 고정
args = TrainingArguments(output_dir="./outputs/07", num_train_epochs=1,
    per_device_train_batch_size=4, per_device_eval_batch_size=4,
    eval_strategy="epoch", save_strategy="epoch", report_to="none", seed=42)

# Trainer: 학습 반복문(순전파 → 손실 → 역전파 → 가중치 갱신)과 평가를 대신 처리
# - processing_class=tok: 저장할 때 토크나이저도 함께 다룬다
# - DataCollatorWithPadding: 배치마다 그 배치에서 가장 긴 문장 길이에 맞춰 패딩
#   (전체 최대 길이로 패딩하는 것보다 계산이 적다)
trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=valid_ds,
    processing_class=tok, data_collator=DataCollatorWithPadding(tokenizer=tok),
    compute_metrics=metrics)

# 학습 실행: 진행률과 함께 eval_loss, eval_accuracy, eval_f1 등이 출력된다
trainer.train()

# 6) 독립 테스트 평가: 학습·검증에 쓰지 않은 test 데이터로 최종 성능을 확인
result = trainer.predict(test_ds)
pred = np.argmax(result.predictions, axis=-1)
# classification_report: 클래스별 precision(정밀도), recall(재현율), f1, support(샘플 수)
# - 데이터가 30행뿐이라 결과가 실행 환경에 따라 조금씩 달라질 수 있다
print("독립 테스트 평가:\n", classification_report(
    result.label_ids, pred, labels=list(labels_dict),
    target_names=list(labels_dict.values()), zero_division=0))

# 7) 저장: 모델 가중치·config와 토크나이저를 같은 폴더에 저장
# → 저장한 폴더를 다시 불러오는 방법은 08_save_reload.py에서 다룬다
trainer.save_model("./saved_model_07")
tok.save_pretrained("./saved_model_07")
print("모델 저장: saved_model_07")
