"""A2-M1-2: RAG 모델 선택 미니 실습 — 모델 비교 -> 검색 -> 근거 기반 생성.
설치: pip install torch transformers openai python-dotenv
실행: python A2_M1_2_mini_rag.py
선택: .env 파일의 OPENAI_API_KEY=... 를 설정하면 생성 모델까지 호출한다.
"""
import os
import time
import torch
import torch.nn.functional as F
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModel

# 1. 문서 원본: A1 규칙의 주제를 단순화한 학습용 데이터이며 실제 rules.csv가 아님.
DOCS = [
    {"id": "R01", "text": "의미 있는 이미지에는 이미지 목적을 설명하는 alt 대체 텍스트가 필요합니다."},
    {"id": "R02", "text": "장식용 이미지에는 문맥에 따라 빈 alt 속성(alt="")을 사용할 수 있습니다."},
    {"id": "R03", "text": "링크 텍스트만으로 링크의 목적을 이해할 수 있도록 작성해야 합니다."},
    {"id": "R04", "text": "입력 필드에는 화면 레이블 또는 접근 가능한 이름을 제공해야 합니다."},
    {"id": "R05", "text": "모호한 '자세히' 링크는 문맥에서 목적이 명확한지 확인해야 합니다."},
]

# 2. 질문마다 '정답 근거 문서 ID'를 미리 지정해야 검색 모델을 평가할 수 있음.
#    현업에서는 도메인 담당자가 정답 데이터를 검수해야 함.
TESTS = [
    {"question": "의미 있는 이미지에 alt가 없으면 무엇을 확인하나요?", "gold": "R01"},
    {"question": "장식용 이미지의 alt를 비워도 되나요?", "gold": "R02"},
    {"question": "입력창에 레이블이 필요한가요?", "gold": "R04"},
]

# 3. 모델 후보: 각각 자신의 토크나이저/임베딩 모델을 한 쌍으로 로딩.
#    두 번째 모델은 비교 실습용이며 다운로드 시간이 더 걸릴 수 있음.
MODEL_IDS = [
    "intfloat/multilingual-e5-small",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
]
TOP_K = 2


def encode_texts(texts, tokenizer, model, prefix=""):
    """문장 -> 토큰 ID -> 은닉 벡터 -> PAD 제외 평균 -> L2 정규화."""
    batch = tokenizer([prefix + t for t in texts],
                      padding=True, truncation=True, max_length=256,
                      return_tensors="pt")
    with torch.inference_mode():  # 추론은 역전파가 필요 없으므로 메모리를 절약
        hidden = model(**batch).last_hidden_state  # (문장 수, 토큰 수, 차원)
    mask = batch["attention_mask"].unsqueeze(-1)  # PAD=0, 실제 토큰=1
    pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
    return F.normalize(pooled, p=2, dim=1)  # 내적을 코사인 유사도로 사용


def search(question, doc_vecs, tokenizer, model, q_prefix=""):
    """질문 벡터와 문서 벡터의 코사인 유사도 상위 문서 반환."""
    q = encode_texts([question], tokenizer, model, q_prefix)
    similarities = (q @ doc_vecs.T)[0]  # 정규화 후 내적 = 코사인 유사도
    scores, indices = torch.topk(similarities, k=min(TOP_K, len(DOCS)))
    return [(DOCS[idx], score) for score, idx in zip(scores.tolist(), indices.tolist())]


def main():
    load_dotenv()  # API 키는 .env로만 관리. 코드에 키 직접 입력 금지.
    reports = []
    best = None

    # 4. 후보별로 같은 문서/질문을 사용해야 공정한 비교가 됨.
    for model_id in MODEL_IDS:
        print("\n=== 모델 후보:", model_id, "===")
        started = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModel.from_pretrained(model_id).eval()
        # e5의 query:/passage: 접두사 정책을 반드시 지킨다.
        is_e5 = "multilingual-e5" in model_id
        q_prefix = "query: " if is_e5 else ""
        p_prefix = "passage: " if is_e5 else ""
        doc_vecs = encode_texts([d["text"] for d in DOCS], tokenizer, model, p_prefix)
        print("문서 벡터 shape:", tuple(doc_vecs.shape))
        print("질문 첫 문장 토큰 수:", len(tokenizer(q_prefix + TESTS[0]["question"])["input_ids"]))

        hits1 = hits2 = 0
        for case in TESTS:
            ranked = search(case["question"], doc_vecs, tokenizer, model, q_prefix)
            retrieved = [doc["id"] for doc, _ in ranked]
            hits1 += int(case["gold"] in retrieved[:1])
            hits2 += int(case["gold"] in retrieved[:2])
            print("질문:", case["question"])
            print("정답:", case["gold"], "검색:", [(d["id"], round(sc, 4)) for d, sc in ranked])
        score1, score2 = hits1 / len(TESTS), hits2 / len(TESTS)
        elapsed = time.perf_counter() - started  # 로딩+인코딩 포함: 순수 추론속도 아님
        reports.append((model_id, score1, score2, elapsed))
        print(f"Hit@1={score1:.2f}, Hit@2={score2:.2f}, 총시간={elapsed:.1f}초")
        # 실제 프로젝트라면 더 많은 평가 질문·품질·비용·라이선스를 함께 비교
        if best is None or (score1, score2) > (best[0], best[1]):
            best = (score1, score2, model_id, tokenizer, model, doc_vecs, q_prefix)

    print("\n=== 모델 비교표 (소규모 교육용 평가) ===")
    for mid, h1, h2, secs in reports:
        print(mid, f"Hit@1={h1:.2f} Hit@2={h2:.2f} 전체={secs:.1f}s")

    # 5. 선정 모델로 검색된 근거가 답변에 어떤 영향을 주는지 확인.
    _, _, selected_id, tokenizer, model, doc_vecs, q_prefix = best
    question = TESTS[0]["question"]
    ranked = search(question, doc_vecs, tokenizer, model, q_prefix)
    context = "\n".join(f"[{doc['id']}] {doc['text']}" for doc, _ in ranked)
    print("\n선정 모델:", selected_id, "\n검색 근거:\n", context)

    # 6. API 키가 없으면 검색 결과까지만 실행하여 비용 없이 원리 확인 가능.
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY 미설정: 생성 단계 생략. .env에 키를 추가하면 실행됩니다.")
        return

    # 7. 생성 모델은 검색 모델과 역할이 다름: 검색 근거를 읽고 문장으로 답함.
    from openai import OpenAI
    client = OpenAI()
    response = client.responses.create(
        model="gpt-4.1-mini",  # 계정에서 이용 가능한 모델로 변경 가능
        instructions=("제공한 근거에만 기반하여 답하세요. 근거가 부족하면 보류하세요. "
                      "근거 문서 ID를 표시하세요. 검색 점수는 정답 확률이 아닙니다."),
        input=f"질문: {question}\n\n검색 근거:\n{context}",
    )
    print("\n[생성 답변]\n", response.output_text)


if __name__ == "__main__":
    main()
