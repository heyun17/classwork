"""교안 09: Hugging Face만 이용하는 코사인 Top-k 검색.
RAG의 Retrieval(검색) 단계를 직접 만들어 본다.
문서들을 미리 벡터로 바꿔 두고, 질문이 들어오면 질문 벡터와 코사인 유사도가 높은 문서를 찾는다.
search() 함수는 10_hf_gpt_rag.py에서 불러와 사용한다.
"""
from core import load, embed

# 검색 대상 문서 (문서 ID, 내용)
# 실제 서비스에서는 수천~수만 개의 문서 조각(chunk)이 들어간다
DOCS = [
    ("R01", "의미 있는 이미지에는 대체 텍스트를 제공한다."),
    ("R02", "장식용 이미지는 빈 alt를 사용할 수 있다."),
    ("R03", "링크 목적은 링크 텍스트 또는 문맥으로 이해할 수 있어야 한다."),
    ("R04", "입력 필드에는 명확한 이름과 레이블이 필요하다."),
]

# E5 임베딩 모델과 토크나이저 불러오기 (core.py 참고)
tok, model = load()

# 문서 벡터는 질문마다 다시 계산할 필요가 없으므로 시작할 때 한 번만 만들어 둔다
# - 문서와 질문에 같은 모델을 사용하되 E5의 접두어를 구분한다
#   문서는 "passage: ", 질문은 "query: "
# - 결과 shape: [문서 수, 384], 각 벡터는 길이 1로 정규화되어 있다
doc_vectors = embed([text for _, text in DOCS], tok, model, kind="passage")


def search(question, top_k=3):
    """질문과 가장 비슷한 문서 top_k개를 (문서 ID, 내용, 점수) 목록으로 돌려준다."""
    # 질문 1개를 벡터로 변환 → [1, 384]이므로 [0]으로 꺼내 [384]로 만든다
    query_vector = embed([question], tok, model, kind="query")[0]
    # L2 정규화된 벡터의 내적 = 코사인 유사도
    # [문서 수, 384] @ [384] → [문서 수]: 모든 문서와의 점수를 한 번에 계산
    scores = doc_vectors @ query_vector
    # argsort(descending=True): 점수가 높은 순으로 문서 번호를 정렬하고, 앞에서 top_k개만 사용
    ids = scores.argsort(descending=True)[:top_k].tolist()
    return [(DOCS[i][0], DOCS[i][1], float(scores[i])) for i in ids]


# 이 파일을 직접 실행할 때만 아래 대화형 검색을 실행한다
# (10번에서 import할 때는 실행되지 않고 search 함수만 가져간다)
if __name__ == "__main__":
    print("문서벡터 shape:", tuple(doc_vectors.shape))
    while True:
        try:
            question = input("\n질문 (q 종료): ").strip()
        except (EOFError, KeyboardInterrupt):
            # 입력이 끝났거나(EOF) Ctrl+C를 누르면 에러 없이 종료
            break
        if question.lower() == "q":
            break
        if not question:
            # 빈 입력은 검색하지 않고 다시 묻는다
            continue
        # 출력: 문서 ID / 코사인 유사도 / 문서 내용 (점수 높은 순)
        # E5는 점수가 전체적으로 높게(0.8 근처) 나오므로 절대값보다 순위를 보는 것이 중요하다
        for doc_id, content, score in search(question):
            print(f"{doc_id} / {score:.4f} / {content}")
