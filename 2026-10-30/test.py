import torch
import torch.nn.functional as F
from transformers import pipeline

# 1. 임베딩 파이프라인 생성
embedder = pipeline(
    task="feature-extraction",
    model="intfloat/multilingual-e5-small",
    framework="pt",
    device=-1
)

# 2. 한국어 텍스트
text = "passage: Docker는 컨테이너를 실행하는 플랫폼이다."

# 3. 임베딩 추출
outputs = embedder(
    text,
    return_tensors=True,
    truncation=True
)

# 4. 토큰 벡터들을 평균하여 문장 벡터 생성
vector = outputs.mean(dim=1)

# 5. 벡터 정규화
vector = F.normalize(vector, p=2, dim=1)

print("벡터 크기:", vector.shape)
print("벡터 앞 10개:", vector[0][:10].tolist())
