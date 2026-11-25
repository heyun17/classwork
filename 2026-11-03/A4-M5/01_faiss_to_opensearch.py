from clients import get_opensearch_client
from vector_service import load_existing_faiss,create_vector_index,transfer_faiss_vectors
from config import RAG_INDEX
c=get_opensearch_client()
index,chunks=load_existing_faiss()
print("FAISS 벡터 수:",index.ntotal)
print("청크 수:",len(chunks))
print("벡터 차원:",index.d)
print("rag_docs 생성:",create_vector_index(c,index.d,recreate=True))
transfer_faiss_vectors(c,index,chunks)
print("OpenSearch 벡터 저장 완료:",c.count(index=RAG_INDEX)["count"],"개")
