import json
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ==================================================
# 경로 / 설정
# ==================================================

chunks_file = r"D:\OneDrive\#classes\November\1105\classwork\data\chunks.jsonl"
chroma_path = r"D:\OneDrive\#classes\November\1105\classwork\data\chroma_db"

EMBED_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "travel_openai"


# ==================================================
# 1. chunks.jsonl 불러오기
# ==================================================

with open(chunks_file, "r", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]


ids = [
    chunk["chunk_id"]
    for chunk in chunks
]

texts = [
    chunk["text"]
    for chunk in chunks
]

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
# 2. OpenAI 임베딩
# ==================================================

openai_client = OpenAI()

response = openai_client.embeddings.create(
    model=EMBED_MODEL,
    input=texts
)

embeddings = [
    item.embedding
    for item in response.data
]


print("\n===== OpenAI 임베딩 =====")
print("임베딩 개수:", len(embeddings))
print("벡터 차원:", len(embeddings[0]))


# ==================================================
# 3. Chroma 저장
# ==================================================

chroma_client = chromadb.PersistentClient(
    path=chroma_path
)

# 이전 실행 결과가 있으면 컬렉션을 지우고 새로 생성
try:
    chroma_client.delete_collection(
        name=COLLECTION_NAME
    )
except Exception:
    pass


collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)


collection.upsert(
    ids=ids,
    documents=texts,
    embeddings=embeddings,
    metadatas=metadatas
)


print("\n===== Chroma 저장 =====")
print("컬렉션:", COLLECTION_NAME)
print("저장된 청크 수:", collection.count())


# ==================================================
# 4. 질문 검색
# ==================================================

question = "노을스테이 호텔 옥상에서는 무엇을 할 수 있나요?"


question_response = openai_client.embeddings.create(
    model=EMBED_MODEL,
    input=[question]
)

question_embedding = [
    question_response.data[0].embedding
]


results = collection.query(
    query_embeddings=question_embedding,
    n_results=5,
    include=[
        "documents",
        "metadatas",
        "distances"
    ]
)


# ==================================================
# 검색 결과 출력
# ==================================================

print("\n===== OpenAI 임베딩 검색 상위 5개 =====")
print("질문:", question)
print()
print(f"{'순위':<6}{'chunk_id':<12}{'category':<18}{'distance(↓ 가까움)'}")

for i in range(len(results["ids"][0])):
    chunk_id = results["ids"][0][i]
    category = results["metadatas"][0][i]["category"]
    distance = results["distances"][0][i]

    print(
        f"{i + 1:<6}"
        f"{chunk_id:<12}"
        f"{category:<18}"
        f"{distance:.4f}"
    )