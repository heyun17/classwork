"""A2-M1-2 마무리: 검색 임베딩 + 코사인 유사도 + 근거 기반 답변 생성.
설치: pip install torch transformers openai python-dotenv
환경: .env 파일에 OPENAI_API_KEY=... (직접 작성, 배포 금지)
실행: python A2_M1_2_mini_rag.py
"""
import os
import torch
import torch.nn.functional as F
from dotenv import load_dotenv
from openai import OpenAI
from transformers import AutoModel, AutoTokenizer

# A1 규칙 설명을 바탕으로 한 학습용 문서 (실제 규칙 원본 파일이 아님)
DOCS = [
    {"id": "R01", "text": "의미 있는 이미지에는 이미지의 목적을 설명하는 alt 대체 텍스트가 필요합니다."},
    {"id": "R02", "text": "장식용 이미지는 문맥에 따라 빈 alt 속성(alt=\"\")으로 처리할 수 있습니다."},
    {"id": "R03", "text": "링크 텍스트만 읽어도 링크의 목적을 이해할 수 있도록 작성해야 합니다."},
    {"id": "R04", "text": "입력 필드에는 화면 표시 레이블 또는 접근 가능한 이름을 제공해야 합니다."},
    {"id": "R05", "text": "모호한 '자세히' 문구는 주변 문맥만으로 목적이 확인되는지 검토해야 합니다."},
]

MODEL_ID = "intfloat/multilingual-e5-small"
QUESTION = "이미지에 대체 텍스트가 없으면 어떤 점을 확인해야 하나요?"
TOP_K = 2


def embeddings(texts, prefix, tokenizer, model):
    batch = tokenizer(
        [prefix + text for text in texts], padding=True,
        truncation=True, max_length=256, return_tensors="pt"
    )
    with torch.inference_mode():
        output = model(**batch).last_hidden_state
    mask = batch["attention_mask"].unsqueeze(-1)
    mean = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
    return F.normalize(mean, p=2, dim=1)


def main():
    load_dotenv()
    print("[1] 임베딩 모델 로딩:", MODEL_ID)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModel.from_pretrained(MODEL_ID).eval()

    print("[2] 문서 벡터 생성")
    doc_vectors = embeddings([d["text"] for d in DOCS], "passage: ", tokenizer, model)
    print("    문서 행렬:", tuple(doc_vectors.shape))

    print("[3] 질문 벡터 생성 → 코사인 유사도 검색")
    query_vector = embeddings([QUESTION], "query: ", tokenizer, model)
    similarities = (query_vector @ doc_vectors.T)[0]  # 정규화 벡터의 내적 = 코사인 유사도
    scores, indices = torch.topk(similarities, k=min(TOP_K, len(DOCS)))
    selected = []
    for score, index in zip(scores.tolist(), indices.tolist()):
        doc = DOCS[index]
        selected.append(doc)
        print(f"    {doc['id']} | {score:.4f} | {doc['text']}")

    print("[4] 검색 근거를 생성 모델에 전달")
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY가 없어 답변 생성을 생략합니다. 위 검색 단계는 정상 완료되었습니다.")
        print(".env 파일에 OPENAI_API_KEY를 지정한 뒤 재실행하면 답변까지 생성됩니다.")
        return

    context = "\n".join(f"[{d['id']}] {d['text']}" for d in selected)
    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        instructions=("제공된 근거에만 기반해 한국어로 간결하게 답하세요. "
                      "근거가 부족하면 '제공된 문서만으로 판단할 수 없습니다'라고 답하세요. "
                      "답변 끝에 참조 문서 ID를 표기하세요. 검색 점수는 정답 확률이 아닙니다."),
        input=f"질문: {QUESTION}\n\n검색된 근거:\n{context}",
    )
    print("[5] 생성 답변:\n", response.output_text)


if __name__ == "__main__":
    main()
