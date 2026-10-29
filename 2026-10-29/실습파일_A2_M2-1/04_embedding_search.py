"""교안 04: Last Hidden State, 패딩 제외 평균, L2 정규화, 코사인 비교.
문장을 하나의 벡터(임베딩)로 바꾸는 과정을 단계별로 확인한다.
모델 출력(토큰별 벡터) → 평균으로 문장 벡터 1개 → 길이 1로 정규화 → 코사인 유사도 비교.
공통 함수(load, embed, mean_pool)는 core.py에 있다.
"""
import torch
from core import load, embed, mean_pool

# load(): core.py의 MODEL_ID(intfloat/multilingual-e5-small) 토크나이저와 모델을 불러온다
# - E5는 문장 임베딩(검색)용으로 학습된 다국어 인코더 모델
tok, model = load()

# 비교할 문장: 앞의 두 개는 비슷한 의미, 세 번째는 전혀 다른 주제
sentences = ["이미지 대체 텍스트", "이미지 alt 설명", "서버 배포 장애"]

# E5 모델은 입력 앞에 용도를 알려 주는 접두어를 붙여야 성능이 제대로 나온다
# - "passage: " → 검색 대상 문서, "query: " → 검색 질문
batch = tok(["passage: " + s for s in sentences], padding=True, truncation=True,
            return_tensors="pt")

# inference_mode: 학습이 아니라 추론만 하므로 기울기(gradient) 계산을 끄고 빠르게 실행
with torch.inference_mode():
    output = model(**batch)
    # last_hidden_state: 마지막 층의 출력. 토큰마다 벡터가 하나씩 있다
    # mean_pool: 토큰 벡터들의 평균을 내 문장 벡터 1개로 만든다
    # - attention_mask를 이용해 [PAD] 토큰은 평균에서 제외한다
    #   (패딩까지 평균에 넣으면 짧은 문장일수록 벡터가 왜곡됨)
    pooled = mean_pool(output.last_hidden_state, batch["attention_mask"])

# shape 변화로 과정을 확인
# - input_ids: [문장 수, 토큰 수]
# - last_hidden_state: [문장 수, 토큰 수, 히든 크기 384] → 토큰마다 384차원 벡터
# - pooled: [문장 수, 384] → 토큰 축을 평균 내서 문장당 벡터 1개
print("input_ids:", tuple(batch["input_ids"].shape))
print("last_hidden_state:", tuple(output.last_hidden_state.shape))
print("pooled:", tuple(pooled.shape))

# embed(): 위 과정(접두어 → 토큰화 → 모델 → mean_pool)에 L2 정규화까지 한 번에 해 주는 함수
# - L2 정규화: 벡터를 길이(norm)로 나눠 길이를 1로 만든다
vec = embed(sentences, tok, model, kind="passage")
print("정규화 문장 벡터:", tuple(vec.shape))

# 정규화 전에는 길이가 제각각(약 4.6), 정규화 후에는 모두 1
# (0.99999994처럼 보이는 것은 부동소수점 오차로, 사실상 1)
print("정규화 전 L2:", [round(x, 4) for x in pooled.norm(dim=1).tolist()])
print("정규화 후 L2:", [round(x, 4) for x in vec.norm(dim=1).tolist()])

# 코사인 유사도 = 두 벡터의 내적 / (길이 × 길이)
# 벡터 길이가 1로 정규화되어 있으므로 내적(@)만 하면 바로 코사인 유사도가 된다
# - vec[0] @ vec.T: 첫 문장 벡터와 모든 문장 벡터의 유사도를 한 번에 계산
# - 1에 가까울수록 의미가 비슷하다. 자기 자신과의 유사도는 1
# - E5 모델은 점수가 전체적으로 높게(0.8~1.0) 나오는 편이라
#   절대값보다 문장 간 순위(어느 쪽이 더 높은지)를 보는 것이 중요하다
print("\n[첫 문장과의 코사인 유사도]")
for s, score in zip(sentences, (vec[0] @ vec.T).tolist()):
    print(f"  {sentences[0]} ↔ {s}: {score:.4f}")
