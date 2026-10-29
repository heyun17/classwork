"""교안 06: CSV → Dataset → DatasetDict, map 배치 및 컬럼 처리.
학습용 데이터를 Hugging Face datasets 형식으로 불러와 train/test로 나누고,
토크나이저를 적용해 모델에 넣을 수 있는 형태(input_ids 등)로 바꾸는 과정을 확인한다.
같은 폴더에 feedback_sample.csv(text, label 컬럼)가 있어야 한다.
"""
from pathlib import Path
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset
from transformers import AutoTokenizer

# Path(__file__).with_name(): 이 py 파일과 같은 폴더의 CSV 경로
# (어느 폴더에서 실행하든 파일을 찾을 수 있다)
csv_file = Path(__file__).with_name("feedback_sample.csv")

# 1) pandas로 CSV 읽기: shape은 (행 수, 컬럼 수)
df = pd.read_csv(csv_file)
print("pandas:", df.shape, df.columns.tolist())

# 2) pandas DataFrame → Hugging Face Dataset
# - preserve_index=False: pandas의 행 번호(index)는 컬럼으로 가져오지 않는다
# - features: 컬럼 목록, num_rows: 행(샘플) 수
base = Dataset.from_pandas(df, preserve_index=False)
print("Dataset:", base)

# 3) train/test 나누기
# - test_size=0.25: 25%를 평가용으로 떼어 낸다 (9행 → train 6 / test 3)
# - seed=42: 섞는 순서를 고정해 실행할 때마다 같은 결과가 나오게 한다
splits = base.train_test_split(test_size=0.25, seed=42)

# DatasetDict: 여러 Dataset을 이름("train", "test")으로 묶어 한 번에 다루는 dict
dsd = DatasetDict({"train": splits["train"], "test": splits["test"]})
print("DatasetDict:", dsd)

# (참고) pandas 없이 load_dataset("csv")로 CSV를 바로 DatasetDict로 불러올 수도 있다
# - data_files에 {"split 이름": 파일 경로}를 주면 그 이름으로 만들어진다
print("load_dataset(csv):", load_dataset("csv", data_files={"train": str(csv_file)}))

# 4) 토크나이저를 데이터셋 전체에 적용
tok = AutoTokenizer.from_pretrained("klue/bert-base")

def encode_batch(batch):
    # batched=True이면 batch["text"]는 문장 1개가 아니라 문장 리스트로 들어온다
    # truncation + max_length=48: 48토큰보다 긴 문장은 잘라낸다
    # (padding은 여기서 하지 않고, 학습할 때 배치 단위로 맞추는 것이 효율적)
    return tok(batch["text"], truncation=True, max_length=48)

# map: 모든 행에 함수를 적용해 반환한 값을 새 컬럼으로 추가한다
# - batched=True: 여러 행을 묶어서 한 번에 처리 (한 줄씩보다 빠름)
# - batch_size=2: 한 번에 2행씩 묶음 (보통은 기본값 1000을 그대로 쓴다)
# - DatasetDict에 적용하면 train, test 모두에 적용된다
tokenized = dsd.map(encode_batch, batched=True, batch_size=2)

# 토크나이저 결과(input_ids, token_type_ids, attention_mask)가 컬럼으로 추가됨
print("추가된 컬럼:", tokenized["train"].column_names)
print("첫 행:", tokenized["train"][0])

# 5) 필요 없는 컬럼 제거
# - 모델은 숫자만 입력받으므로 원문 text 컬럼은 학습할 때 필요 없다
# - remove_columns는 새 데이터셋을 돌려줄 뿐, 원래 데이터셋은 그대로 둔다
removed = tokenized.remove_columns(["text"])
print("text 컬럼을 제거한 결과:", removed["train"].column_names)
print("원본 데이터셋은 변경되지 않습니다:", dsd["train"].column_names)
