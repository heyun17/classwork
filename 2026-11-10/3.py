from dotenv import load_dotenv                                   # ⓪ .env 로더
from langchain_openai import ChatOpenAI                          # ① 모델
from langchain_core.prompts import ChatPromptTemplate            # ② 프롬프트
from langchain_core.output_parsers import StrOutputParser        # ③ 파서

# ⓪ .env 파일에서 API 키 불러오기
#    .env 파일에 OPENAI_API_KEY=키값 으로 적혀 있어야 함
load_dotenv()

# ① 모델
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ② 프롬프트 — {role}, {question}은 실행할 때 채울 빈칸
prompt = ChatPromptTemplate.from_template(
    "당신은 {role} 전문가입니다. {question}에 답해주세요."
)

# ③ 출력 파서 — 모델의 답에서 글자만 꺼냄
parser = StrOutputParser()

# ④ 체인 — 프롬프트 → 모델 → 파서 순서로 연결
chain = prompt | llm | parser

# ⑤ 실행 — 빈칸 이름과 같은 키로 값을 넣음
data = {"role": "건강", "question": "여름철식중독"}
result = chain.invoke(data)
print(result)