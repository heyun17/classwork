
import faiss
import numpy as np
import torch
from transformers import pipeline

# 1. 샘플 문서
texts = [
    "Docker는 애플리케이션을 컨테이너로 실행하는 플랫폼이다.",
    "Docker Image는 컨테이너를 생성하기 위한 템플릿이다.",
    "Docker Compose는 여러 컨테이너를 함께 관리한다.",
    "Kubernetes는 컨테이너 배포와 확장을 자동화한다.",
    "PostgreSQL은 관계형 데이터베이스 관리 시스템이다.",
    "FastAPI는 Python으로 API 서버를 만드는 프레임워크다.",
    "Dockerfile은 Docker 이미지를 빌드하는 설정 파일이다.",
    "컨테이너는 이미지로부터 생성되는 실행 인스턴스다.",
]

# 2. Hugging Face 임베딩 파이프라인
embedder = pipeline(
    "feature-extraction",
    model="intfloat/multilingual-e5-small",
    framework="pt",
    device=-1
)

# 3. 문장 임베딩 함수
def embed(text, prefix="passage: "):
    result = embedder(
        prefix + text,
        return_tensors=True,
        truncation=True
    )

    # 토큰 벡터 평균 (패딩 없는 단일 문장 입력)
    return result.mean(dim=1)[0].numpy()

# 4. 문서 벡터 생성
vectors = np.array(
    [embed(text) for text in texts],
    dtype="float32"
)

# 5. 정규화 전 확인
print("정규화 전 원소 합:", np.sum(vectors[0]))
print("정규화 전 L2 길이:", np.linalg.norm(vectors[0]))

# 6. L2 정규화
faiss.normalize_L2(vectors)

# 7. 정규화 후 확인
print("정규화 후 원소 합:", np.sum(vectors[0]))
print("정규화 후 L2 길이:", np.linalg.norm(vectors[0]))

# 8. FAISS IVF 인덱스 생성
dimension = vectors.shape[1]
nlist = 2

index = faiss.IndexIVFFlat(
    faiss.IndexFlatIP(dimension),
    dimension,
    nlist,
    faiss.METRIC_INNER_PRODUCT
)

# 9. 클러스터 학습 및 저장
index.train(vectors)
index.add(vectors)
index.nprobe = 2

# 10. 샘플 질문
question = "Docker Image와 Container는 어떤 관계야?"

query_vector = np.array(
    [embed(question, prefix="query: ")],
    dtype="float32"
)

faiss.normalize_L2(query_vector)

print("\n질문 벡터 L2 길이:", np.linalg.norm(query_vector[0]))

# 11. 코사인 유사도 검색
scores, indices = index.search(query_vector, k=3)

print("\n질문:", question)
print("\n검색 결과:")

for score, idx in zip(scores[0], indices[0]):
    if idx != -1:
        print(f"\n코사인 유사도: {score:.4f}")
        print(f"문서: {texts[idx]}")

# 12. FAISS 코사인 유사도 Top 2 검색
scores, indices = index.search(query_vector, k=2)

print("\n===== FAISS 검색 TOP 2 =====")

for rank, (score, idx) in enumerate(
    zip(scores[0], indices[0]), start=1
):
    if idx != -1:
        print(f"\nTOP {rank}")
        print(f"코사인 유사도: {score:.4f}")
        print(f"문서: {texts[idx]}")