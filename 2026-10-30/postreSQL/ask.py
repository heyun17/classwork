
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("intfloat/multilingual-e5-small")
conn = psycopg.connect("host=localhost dbname=ragdb user=postgres password=pass")
register_vector(conn)

while (text := input("\n질문 (종료: q) > ").strip()) != "q":
    q = model.encode("query: " + text, normalize_embeddings=True)
    question, answer, phone = conn.execute(
        "SELECT question, answer, manager_phone FROM faq ORDER BY embedding <=> %s LIMIT 1", (q,)).fetchone()
    print(f"답변: {answer}\n관련 FAQ: {question}\n담당자: {manager_phone}")
