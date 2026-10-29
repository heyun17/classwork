"""교안 10: 09의 Hugging Face 검색 재사용 + GPT API 응답.
RAG(Retrieval-Augmented Generation) 전체 흐름을 완성한다.
  (1) Retrieval: 09의 임베딩 검색으로 질문과 관련된 문서를 찾고
  (2) Augmentation: 찾은 문서를 근거(context)로 프롬프트에 붙여
  (3) Generation: GPT가 그 근거만 사용해 답변을 생성한다
같은 폴더의 .env 파일에 OPENAI_API_KEY가 있어야 한다 (.env.example 참고).
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from importlib import import_module

# load_dotenv: .env 파일의 값(OPENAI_API_KEY, OPENAI_MODEL)을 환경변수로 불러온다
# - API 키를 코드에 직접 쓰지 않고 .env에 따로 두면 코드 공유 시 키가 노출되지 않는다
load_dotenv()
# 키가 없으면 무거운 임베딩 모델을 불러오기 전에 바로 종료
if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit(".env에 OPENAI_API_KEY를 설정해야 합니다.")

# 파일명이 숫자로 시작하면 "import 09_hf_cosine_search"처럼 쓸 수 없으므로
# importlib로 검색 모듈을 불러온다
# - 이때 09 파일의 모델 로드와 문서 벡터 생성이 실행된다 (대화형 검색 부분은 실행 안 됨)
search = import_module("09_hf_cosine_search").search

try:
    question = input("질문: ").strip()
except (EOFError, KeyboardInterrupt):
    question = ""
if not question:
    raise SystemExit("질문을 입력하세요.")

# (1) Retrieval: 임베딩 모델과 코사인 유사도로 관련 문서 top_k개 검색
# - top_k가 너무 작으면 필요한 근거를 놓치고, 너무 크면 관련 없는 내용이 섞여 답변이 흐려진다
results = search(question, top_k=2)
for doc_id, text, score in results:
    print(f"검색: {doc_id} / {score:.4f} / {text}")

# (2) Augmentation: 생성 모델에 전달할 근거 본문 만들기
# - 문서마다 [R01] 같은 ID를 붙여 두면 GPT가 답변에 출처를 표시할 수 있다
# - 유사도 점수는 "질문과 얼마나 비슷한가"일 뿐, 정답일 확률이 아니므로 GPT에는 넘기지 않는다
context = "\n".join(f"[{doc_id}] {text}" for doc_id, text, score in results)

# (3) Generation: GPT API가 검색된 근거를 사용해 답변을 생성
# - OpenAI(): 환경변수 OPENAI_API_KEY를 자동으로 읽는다
client = OpenAI()
# responses.create: OpenAI Responses API 호출
# - model: .env의 OPENAI_MODEL을 사용하고, 없으면 gpt-4.1-mini
# - instructions: 모델의 행동 규칙 (시스템 프롬프트 역할)
#   "근거만 사용", "모르면 모른다고 말하기"는 환각(hallucination)을 줄이기 위한 지시
# - input: 실제 질문과 검색된 근거
response = client.responses.create(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    instructions="검색된 근거만 사용해 답하세요. 근거가 부족하면 모른다고 말하고 근거 문서 ID를 붙이세요.",
    input=f"질문: {question}\n\n검색 근거:\n{context}",
)
# output_text: 응답에서 생성된 텍스트만 꺼낸다
print("\n답변:\n", response.output_text)
