import json
import chromadb

from openai import OpenAI
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


# .env의 OPENAI_API_KEY 불러오기
load_dotenv()

# ==================================================
# 경로 / 설정
# ==================================================

chunks_file = r"D:\OneDrive\#classes\November\1105\classwork\data\chunks.jsonl"
chroma_path = r"D:\OneDrive\#classes\November\1105\classwork\data\chroma_db"

OPENAI_MODEL = "text-embedding-3-small"
HF_MODEL = "intfloat/multilingual-e5-small"

OPENAI_COLLECTION = "travel_openai"
HF_COLLECTION = "travel_e5"

question = "노을스테이 호텔 옥상에서는 무엇을 할 수 있나요?"


# ==================================================
# 1. chunks.jsonl 불러오기
# ==================================================

with open(chunks_file, "r", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

ids = [chunk["chunk_id"] for chunk in chunks]
texts = [chunk["text"] for chunk in chunks]

metadatas = [
    {
        "doc_id": chunk["doc_id"],
        "category": chunk["category"]
    }
    for chunk in chunks
]

print("===== 청크 불러오기 =====")
print("청크 수:", len(chunks))


# ==================================================
# 2. 기존 OpenAI 컬렉션 불러오기
# ==================================================

chroma_client = chromadb.PersistentClient(
    path=chroma_path
)

openai_collection = chroma_client.get_collection(
    name=OPENAI_COLLECTION
)

print("\n===== OpenAI 컬렉션 =====")
print("저장된 청크 수:", openai_collection.count())


# ==================================================
# 3. Hugging Face e5 모델 불러오기
# ==================================================

print("\n===== Hugging Face 모델 불러오기 =====")

hf_model = SentenceTransformer(
    HF_MODEL
)

print("모델:", HF_MODEL)


# ==================================================
# 4. 청크 임베딩
#
# e5 규칙:
# 문서 앞에는 "passage: "
# ==================================================

passage_texts = [
    "passage: " + text
    for text in texts
]

hf_embeddings = hf_model.encode(
    passage_texts,
    normalize_embeddings=True
)

print("\n===== Hugging Face 임베딩 =====")
print("임베딩 개수:", len(hf_embeddings))
print("벡터 차원:", hf_embeddings.shape[1])


# ==================================================
# 5. Hugging Face용 새 Chroma 컬렉션 생성
# ==================================================

try:
    chroma_client.delete_collection(
        name=HF_COLLECTION
    )
except Exception:
    pass


hf_collection = chroma_client.get_or_create_collection(
    name=HF_COLLECTION
)


hf_collection.upsert(
    ids=ids,

    # Chroma document에는 passage: 를 붙이지 않음
    documents=texts,

    embeddings=hf_embeddings.tolist(),

    metadatas=metadatas
)


print("\n===== Hugging Face Chroma 저장 =====")
print("컬렉션:", HF_COLLECTION)
print("저장된 청크 수:", hf_collection.count())


# ==================================================
# 6. 같은 질문을 각각의 모델로 임베딩
# ==================================================

# OpenAI 질문 임베딩
openai_client = OpenAI()

openai_response = openai_client.embeddings.create(
    model=OPENAI_MODEL,
    input=[question]
)

openai_question_embedding = [
    openai_response.data[0].embedding
]


# Hugging Face 질문 임베딩
# e5 질문 앞에는 "query: "
hf_question_embedding = hf_model.encode(
    ["query: " + question],
    normalize_embeddings=True
).tolist()


# ==================================================
# 7. 각각 상위 5개 검색
# ==================================================

openai_results = openai_collection.query(
    query_embeddings=openai_question_embedding,
    n_results=5,
    include=[
        "metadatas",
        "distances"
    ]
)


hf_results = hf_collection.query(
    query_embeddings=hf_question_embedding,
    n_results=5,
    include=[
        "metadatas",
        "distances"
    ]
)


# ==================================================
# 8. 모델 비교 출력
# ==================================================

print("\n===== OpenAI / Hugging Face 검색 결과 비교 =====")
print("질문:", question)
print()

print(
    f"{'순위':<6}"
    f"{'OpenAI(1536차원)':<25}"
    f"{'Hugging Face e5(384차원)'}"
)

for i in range(5):

    openai_id = openai_results["ids"][0][i]
    openai_distance = openai_results["distances"][0][i]

    hf_id = hf_results["ids"][0][i]
    hf_distance = hf_results["distances"][0][i]

    openai_text = f"{openai_id} {openai_distance:.4f}"
    hf_text = f"{hf_id} {hf_distance:.4f}"

    print(
        f"{i + 1:<6}"
        f"{openai_text:<25}"
        f"{hf_text}"
    )