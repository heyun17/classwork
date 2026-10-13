# -*- coding: utf-8 -*-
"""
에이전트개념.ipynb -> 학습용 Python 변환본

- 원본 노트북의 코드와 설명을 최대한 유지했습니다.
- VS Code에서는 `# %%` 단위로 셀처럼 실행할 수 있습니다.
- `!pip install ...` 같은 노트북 전용 문법은 일반 Python 파일에서 오류가 나므로 주석으로 바꿨습니다.
- 원본 PRODUCTS 데이터에는 `stock` 키가 없지만 check_stock()은 `p["stock"]`을 사용합니다.
  따라서 재고 확인 부분은 원본 그대로 실행하면 KeyError가 발생할 수 있습니다.
  원본에 실제 재고 수량이 제시되지 않았으므로 임의 값을 추가하지 않았습니다.
- STEP 6 원본은 모델에게 checkout 도구를 제시하고 응답을 받는 데까지이며, 반환된 tool_call을
  실제 checkout() 함수로 실행하는 코드는 포함되어 있지 않습니다. 아래 설명에도 이 점을 표시했습니다.
"""


# ==============================================================================
# PART 0. 전체 개요
# ==============================================================================
# 설명: 에이전트의 핵심 공식(LLM + Tools + Loop)과 실습 전체 흐름을 먼저 봅니다.

# %% [markdown]
# # 1교시 실습 · 진짜로 일하는 쇼핑몰 에이전트
# ## 에이전트의 원리, 그리고 현실의 문제들
#
# > **핵심 공식:** `Agent = LLM + Tools + Loop`
# >
# > 도구 몇 개를 쥐여주면, 흐름은 **모델이 알아서** 만듭니다.
# > "키보드 재고 있어? 3개 사면 얼마야?" 한 마디에 모델이 *검색 → 재고확인 → 가격계산*을
# > 스스로 순서대로 호출합니다. 우리는 순서를 짜주지 않습니다.
#
# ---
#
# ### 이 노트북의 두 막(幕)
#
# **1막 — 기본 에이전트 만들기 (STEP 1~3)**
# 도구 3개 + 루프 하나로 "스스로 도구를 골라 쓰는" 에이전트를 만듭니다. 놀랍도록 간단합니다.
#
# **2막 — 그런데 현실은 호락호락하지 않다 (STEP 4~7)**
# 기본 에이전트엔 구멍이 많습니다. 하나씩 터뜨려 보고, 하나씩 막습니다.
#
# | STEP | 문제 | 해결 |
# |------|------|------|
# | **4** | 모델이 **없는 상품명**을 지어내 호출 (환각) | 함수 안에서 검증 + *힌트 담은 에러* |
# | **5** | 도구가 **에러**를 뱉으면 멈춰버림 | 에러를 *결과로 되먹여* 모델이 스스로 복구 |
# | **6** | **결제** 같은 되돌릴 수 없는 행동 | 실행 직전 *사람 확인* (휴먼인더루프) |
# | **7** | 루프가 **무한히** 돌면? 비용은? | `max_turns` 상한 + 관찰(LangSmith) |
#
# > 💡 이게 1교시의 진짜 메시지입니다 — **에이전트의 뼈대는 쉽다. 어려운 건 그 뼈대를 현실에서 안전하게 굴리는 것이다.**

# ==============================================================================
# PART 1. 환경 준비와 API 연결
# ==============================================================================
# 설명: .env에서 API 키를 읽고 OpenAI API가 정상 호출되는지 확인합니다.

# %% [markdown]
# ---
# ## STEP 0 · 환경 준비
#
# `.env` 파일에 발급받은 `OPENAI_API_KEY`를 사용하여 임베딩(상품 검색)과 gpt-4를 실행합니다.
# -  env파일을 구글 드라이브 폴더에 업로드 합니다.
#   - .env 파일 내용
#           - OPENAI_API_KEY=sk-proj-t...
#           - ANTHROPIC_API_KEY=sk-ant-api03-...;.

# %%
# 노트북 전용 명령 변환: 터미널에서 실행 -> pip install -U langchain
# 노트북 전용 명령 변환: 터미널에서 실행 -> pip install -U langchain-openai
# 노트북 전용 명령 변환: 터미널에서 실행 -> pip install -U langchain-anthropic
# 노트북 전용 명령 변환: 터미널에서 실행 -> pip install -U langchain-community
# 노트북 전용 명령 변환: 터미널에서 실행 -> pip install -U faiss-cpu
# 노트북 전용 명령 변환: 터미널에서 실행 -> pip install -U python-dotenv

# %%
from dotenv import load_dotenv
load_dotenv(".env", override=True)

# %%
# api키 잘 읽혔는지 확인용
import os

openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

print(
    "OpenAI:",
    openai_key[:12] + "..." if openai_key else "불러오기 실패"
)

print(
    "Anthropic:",
    anthropic_key[:12] + "..." if anthropic_key else "불러오기 실패"
)

# %%
# 샘플로 gptAPI 실행
from dotenv import load_dotenv
from openai import OpenAI

# .env 읽기
load_dotenv()

# OpenAI 클라이언트 생성
client = OpenAI()

# GPT 호출
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": "안녕하세요. 자기소개 해주세요."
        }
    ]
)

print(response.choices[0].message.content)

# ==============================================================================
# PART 2. 상품 데이터와 벡터 검색
# ==============================================================================
# 설명: 상품명을 임베딩해 FAISS에 저장하고 자연어로 비슷한 상품을 찾습니다. 마지막에는 도구 없이 LLM만 호출했을 때의 한계도 확인합니다.
# 주의: PRODUCTS에는 stock 값이 정의되어 있지 않습니다. 이후 check_stock()과 연결할 때 확인하세요.

# %% [markdown]
# ---
# # 1막 · 기본 에이전트 만들기
#
# ## STEP 1 · 상품 데이터 + 검색 준비
#
# 상품 목록은 임의로 작성. 상품명을 임베딩해 FAISS에 넣으면
# *"키보드"* 라고만 쳐도 *"기계식 키보드"* 를 의미로 찾아줍니다.

# %%
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# %%
PRODUCTS = {
    "무선 블루투스 이어폰": {
        "price": 39000,
        "description": "가볍고 휴대하기 좋은 무선 이어폰"
    },
    "노이즈 캔슬링 헤드폰": {
        "price": 159000,
        "description": "외부 소음을 줄여주는 오버이어 헤드폰"
    },
    "휴대용 보조배터리": {
        "price": 29000,
        "description": "스마트폰 충전을 위한 10000mAh 보조배터리"
    },
    "게이밍 기계식 키보드": {
        "price": 89000,
        "description": "게임과 문서 작업에 적합한 기계식 키보드"
    }
}

# %%
# 오픈 API임베딩 모델 지정
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# %%
PRODUCTS.keys()

# %%
# 상품명을 벡터 db에 저장
product_names = list(PRODUCTS.keys())
print(product_names)

vectordb = FAISS.from_texts(
    texts=product_names,
    embedding=embedding_model
)
print(vectordb)

print("상품", len(PRODUCTS), "개 적재 완료")

# %%
# 상품검색

user_query = "출퇴근할 때 음악을 들을 수 있는 제품"
search_results = vectordb.similarity_search(
    query=user_query,
    k=2
)

search_results

# %%
for document in search_results:
    print(document.page_content)

# %%
query="기계식 키보드 재고 있어? 3개 사면 얼마야?"

# 도구 없이, 그냥 LLM한테만 물어본다
msg = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content":query }]
).choices[0].message
print(msg.content)

# ==============================================================================
# PART 3. 에이전트 도구와 Tool Schema
# ==============================================================================
# 설명: 파이썬 함수를 실제 도구로 만들고, LLM이 도구 사용법을 이해할 수 있도록 JSON 스키마를 정의합니다.

# %% [markdown]
# ## STEP 2 · 에이전트 작성
# - 여러 gpt툴 작성
#   - `search_product` — 상품 검색 (임베딩)
#   - `check_stock` — 재고 확인
#   - `calc_price` — 가격 계산 (3개 이상 10% 할인)

# %%
def search_product(query):
    return [d.page_content for d in vectordb.similarity_search(query, k=2)]

def check_stock(name):
    p = PRODUCTS.get(name)
    return f"{name}: 재고 {p['stock']}개" if p else f"{name}: 없는 상품"

def calc_price(name, qty):
    p = PRODUCTS.get(name)
    if not p:
        return f"{name}: 없는 상품"
    total = p["price"] * qty
    if qty >= 3:
        total = int(total * 0.9)     # 3개 이상 10% 할인
    return f"{name} {qty}개 = {total}원"

TOOLS = {"search_product": search_product,
         "check_stock": check_stock,
         "calc_price": calc_price}
print(" 도구 3개 준비")

# %% [markdown]
# 각 도구의 **설명서(JSON 스키마)** 도 만듭니다. 모델은 이 `description`만 보고
# "언제 이 도구를 쓸지" 판단합니다 — **description = 성능**입니다.

# %%
tools = [
  {"type":"function","function":{"name":"search_product",
    "description":"상품을 검색한다. 사용자가 물건을 찾거나 추천을 원할 때 사용.",
    "parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},

  {"type":"function","function":{"name":"check_stock",
    "description":"상품의 재고를 확인한다. 반드시 정확한 상품명을 넣을 것.",
    "parameters":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}}},

  {"type":"function","function":{"name":"calc_price",
    "description":"상품 N개의 총 가격을 계산한다(3개 이상 10% 할인).",
    "parameters":{"type":"object","properties":{"name":{"type":"string"},"qty":{"type":"integer"}},"required":["name","qty"]}}},
]
print(" 스키마 준비")

# ==============================================================================
# PART 4. 에이전트 루프와 토큰 사용량
# ==============================================================================
# 설명: LLM이 도구를 선택하는 동안 반복하고, 도구 결과를 다시 모델에게 전달하는 기본 Agent Loop를 구현합니다. 에이전트가 일반 호출보다 토큰을 더 쓰는 이유도 확인합니다.

# %% [markdown]
# ## STEP 3 · 에이전트 루프 = 한 함수
#
# 패턴은 단순합니다: **모델이 도구를 부르는 한 계속 돌고, 안 부르면(=답할 준비됨) 멈춥니다.**
# `max_turns`는 무한루프를 막는 안전장치예요 (STEP 7에서 자세히).

# %%
def run_agent(question, max_turns=6):
    messages = [{"role": "user", "content": question}]
    for _ in range(max_turns):
        msg = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools).choices[0].message
        messages.append(msg)

        if not msg.tool_calls:                 # 도구 안 부름 → 최종 답
            return msg.content

        for call in msg.tool_calls:            # 부른 도구 실행 → 결과 되먹임
            args = json.loads(call.function.arguments)
            result = TOOLS[call.function.name](**args)
            print(f"  🔧 {call.function.name}({args}) → {result}")
            messages.append({"role":"tool", "tool_call_id":call.id,
                             "content":json.dumps(result, ensure_ascii=False)})
    return " 최대 단계 수 초과"

print(" 에이전트 완성")

# %%
PRODUCTS

# %%
# 3개이상은 10%할인함수 들어가 있음
import json

query="기계식 키보드 재고 있어? 3개 사면 얼마야?"
print(run_agent(query))

# %%
query="기계식 키보드 재고 있어? 2개 사면 얼마야?"
print(run_agent(query))

# %% [markdown]
# ## [토큰비교]

# %%
q = "기계식 키보드 재고 있어? 3개 사면 얼마야?"

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": q}]
)
u = resp.usage
print("=== 도구 없이 (1회 호출) ===")
print(f"입력 {u.prompt_tokens} + 출력 {u.completion_tokens} = 총 {u.total_tokens} 토큰")

# %%
def run_agent_with_usage(question, max_turns=6):
    messages = [{"role": "user", "content": question}]
    total_in = total_out = calls = 0
    for _ in range(max_turns):
        resp = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools)
        u = resp.usage
        total_in += u.prompt_tokens          # ← 매 턴 토큰 누적
        total_out += u.completion_tokens
        calls += 1
        msg = resp.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            print("=== 에이전트 (도구 주고) ===")
            print(f"LLM 호출 {calls}회")
            print(f"입력 {total_in} + 출력 {total_out} = 총 {total_in+total_out} 토큰")
            return msg.content
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = TOOLS[call.function.name](**args)
            messages.append({"role":"tool","tool_call_id":call.id,
                             "content":json.dumps(result, ensure_ascii=False)})

run_agent_with_usage(q)

# %% [markdown]
# ###  핵심
# 질문 하나에 모델이 **`search_product` → `check_stock` → `calc_price`** 를 *스스로 순서대로* 불렀습니다.
# 모델이 또 부르고 싶어 하는 한 계속 도는 것.
#
# > 검색 한 번이면 에이전트가 필요 없습니다(그냥 RAG). **경로가 상황마다 달라질 때** 비로소 에이전트가 값을 합니다.
#
# ---
# ---
# # 2막 · 그런데 현실은 호락호락하지 않다
#
# 방금 건 "잘 풀리는 경우"였습니다. 이제 **일부러 망가뜨려** 보고, 막아 봅니다.

# ==============================================================================
# PART 5. 환각 방어: 함수 검증과 힌트
# ==============================================================================
# 설명: 모델이 존재하지 않는 상품명을 만들어 호출할 때, 함수 내부 검증과 설명적인 에러 메시지로 스스로 복구하게 합니다.

# %% [markdown]
# ## STEP 4 · 문제 ① — 환각 (없는 상품명을 지어냄)
#
# 모델은 완벽하지 않습니다. 사용자가 *"맥북 재고 있어?"* 라고 물으면, 우리 상점에 없는데도
# 모델이 `check_stock("맥북")` 처럼 **존재하지 않는 인자를 지어내** 호출할 수 있습니다.

# %%
# 우리 상점에 없는 상품을 물어본다
print(run_agent("맥북 프로 재고 있어?"))

# %% [markdown]
# 지금 `check_stock`은 `"맥북: 없는 상품"` 이라고만 답합니다.
# **해결: 함수 안에서 검증하고, 에러에 "어떻게 고치라"는 힌트를 담는다.**
# 모델을 못 믿으니 **코드가 가드레일**이 됩니다.

# %%
def check_stock(name):
    p = PRODUCTS.get(name)
    if not p:
        # ↓ 그냥 '없음'이 아니라, 다음 행동을 유도하는 힌트를 준다
        return f"'{name}'은(는) 취급하지 않는 상품입니다. search_product로 비슷한 상품을 먼저 찾으세요."
    return f"{name}: 재고 {p['stock']}개"

TOOLS["check_stock"] = check_stock     # 교체
print(run_agent("맥북 프로 재고 있어?"))

# %% [markdown]
# ### 🔎 관찰
# 이제 모델이 *"맥북은 없지만, 대신 이런 상품이 있어요"* 식으로 **스스로 복구**합니다.
# 힌트를 읽고 `search_product`를 불러 대안을 찾기 때문입니다. **에러 메시지가 곧 모델에게 주는 지시**예요.

# ==============================================================================
# PART 6. 도구 실행 에러 복구
# ==============================================================================
# 설명: Tool 실행 자체가 예외를 발생시켜도 Agent Loop가 죽지 않도록 try/except로 감싸고, 에러를 다시 모델에게 전달합니다.

# %% [markdown]
# ## STEP 5 · 문제 ② — 도구가 진짜 에러를 뱉으면?
#
# STEP 4는 "정상적으로 없음을 알리는" 경우였습니다. 그런데 도구 코드가 **진짜로 터지면**
# (잘못된 타입, 외부 API 실패 등) 루프 전체가 죽어버립니다.
#
# **해결: 실행을 `try/except`로 감싸고, 에러조차 도구 결과로 되먹인다.**
# 그러면 모델이 에러 메시지를 읽고 인자를 고쳐 **다시 시도**합니다.

# %%
def run_agent(question, max_turns=6):
    messages = [{"role": "user", "content": question}]
    for _ in range(max_turns):
        msg = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools).choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            try:
                result = TOOLS[call.function.name](**args)
            except Exception as e:
                result = f"에러: {e}. 인자를 확인하고 다시 시도하세요."   # ← 죽지 않고 되먹임
            print(f"  🔧 {call.function.name}({args}) → {result}")
            messages.append({"role":"tool", "tool_call_id":call.id,
                             "content":json.dumps(result, ensure_ascii=False)})
    return "⚠️ 최대 단계 수 초과"

print(" 에러를 되먹이는 루프로 교체 완료")

# %%
# 일부러 잘 터지는 도구를 추가해, 모델이 복구하는지 본다
def divide_price(name, people):
    # people=0 이면 ZeroDivisionError 가 난다 (의도된 버그)
    return f"{name} 1인당 {PRODUCTS[name]['price'] // people}원"

TOOLS["divide_price"] = divide_price
tools.append({"type":"function","function":{"name":"divide_price",
    "description":"상품 가격을 인원수로 나눠 1인당 부담액을 계산한다.",
    "parameters":{"type":"object","properties":{
        "name":{"type":"string"},"people":{"type":"integer"}},"required":["name","people"]}}})

# 0으로 나누게 유도 → 에러 → 모델이 읽고 되묻거나 보정
print(run_agent("기계식 키보드를 0명이서 나눠 내면 1인당 얼마야?"))

# %% [markdown]
# ### 🔎 관찰
# 도구가 `ZeroDivisionError`로 터졌지만 **루프는 죽지 않았습니다.** 에러가 `role:"tool"` 로 모델에게 전달되고,
# 모델은 그걸 읽고 *"0명으로는 나눌 수 없어요"* 라고 사용자에게 되묻거나 보정합니다.
# **사람이 빨간 에러를 보고 코드를 고치는 것과 똑같아요.**

# ==============================================================================
# PART 7. Human-in-the-loop
# ==============================================================================
# 설명: 결제처럼 되돌리기 어려운 쓰기 작업은 LLM이 선택하더라도 실제 실행 직전에 사용자의 확인을 받는 패턴을 봅니다.
# 주의: 원본 STEP 6은 tool_call 선택까지 보여주며 실제 checkout 함수 실행 단계는 빠져 있습니다.

# %% [markdown]
# ## STEP 6 · 문제 ③ — 되돌릴 수 없는 행동 (결제)
#
# 지금까지 도구는 전부 **읽기**(검색·조회·계산)였습니다. 막 불러도 안전했죠.
# 그런데 **결제·주문·메일발송**은 **부작용**이 있습니다. 한 번 실행되면 끝이에요.
# 모델이 환각으로 `checkout`을 부르면? 실제 돈이 빠져나갑니다.
#
# **해결: 휴먼인더루프 — 실행 직전에 사람 확인을 끼운다.**
# 1교시에서 배운 *"모델은 의도만 주고, 실행은 우리가 한다"* 는 분리 덕분에 가능합니다.
# 실행이 우리 손 안에 있으니, 그 직전에 `input()`으로 사람에게 묻습니다.

# %%
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(".env", override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# %% [markdown]
# ## TOOLS
# → GPT가 선택한 이름에 따라 실제 파이썬 함수를 실행
#
# ## tool_definitions
# → GPT에게 어떤 함수가 있고 어떤 인수를 넣어야 하는지 설명

# %%
TOOLS = {}
tool_definitions = []

def checkout(name, qty):
    answer = input(
        f"⚠️ [{name} {qty}개] 결제를 진행할까요? (y/n): "
    )

    if answer.strip().lower() != "y":
        return "사용자가 결제를 취소했습니다."

    return f"결제 완료: {name} {qty}개"

# 실제 실행 함수 등록
TOOLS["checkout"] = checkout


# GPT에게 알려줄 함수 설명 등록
tool_definitions.append({
    "type": "function",
    "function": {
        "name": "checkout",
        "description": (
            "실제 결제를 실행한다. "
            "사용자가 구매 또는 결제를 명확히 요청할 때만 사용한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "결제할 정확한 상품명"
                },
                "qty": {
                    "type": "integer",
                    "description": "결제할 수량"
                }
            },
            "required": ["name", "qty"]
        }
    }
})

# %%
messages = [
    {
        "role": "system",
        "content": "너는 상품 판매 AI이다."
    },
    {
        "role": "user",
        "content": "USB-C 허브 2개 결제해줘"
    }
]


response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages,
    tools=tool_definitions,
    tool_choice="auto"
)

# %% [markdown]
# ### 🔎 관찰
# 모델이 `checkout`을 부르고 싶어도, **사람이 `y`를 누르기 전엔 결제가 일어나지 않습니다.**
# 이 패턴을 **휴먼인더루프(human-in-the-loop)** 라고 합니다.
#
# > 🔑 실무 원칙: **읽기 도구는 자유롭게, 쓰기(부작용) 도구는 사람 확인을 거쳐서.**
# > (이 "쓰기 도구는 특별 취급" 개념은 이후 캐싱·권한 설계로 이어집니다.)

# ==============================================================================
# PART 8. 무한루프·비용·관찰
# ==============================================================================
# 설명: max_turns로 루프 길이를 제한하고, Agent의 토큰 비용과 LangSmith 같은 observability 도구가 필요한 이유를 정리합니다.

# %% [markdown]
# ## STEP 7 · 문제 ④ — 무한루프와 비용
#
# 모델이 잘못된 인자로 **같은 도구를 계속 재시도**하는 루프에 빠질 수 있습니다
# (틀린 인자 → 에러 → 같은 틀린 인자 → …). 상한이 없으면 **비용과 시간이 폭주**합니다.
#
# **해결 1: `max_turns` 상한.** 사실 우리 루프엔 이미 있습니다 — `for _ in range(max_turns)` 의 그 숫자예요.

# %%
# max_turns 를 1로 낮추면, 도구를 다 부르기도 전에 강제 종료된다
print("max_turns=1 (일부러 모자라게):")
print(run_agent("키보드 재고 보고 3개 가격까지 계산해줘", max_turns=1))

# %% [markdown]
# 왜 비용이 무서운가 — 에이전트는 **매 턴 전체 대화를 다시 보냅니다.**
# 루프가 길어질수록 토큰이 *곱*으로 불어나요. 그래서 실무에선 턴 수뿐 아니라
# **총 토큰·총 비용에도 상한**을 둡니다.
#
# **해결 2: 관찰(observability).** 지금 우리는 `print`로 손수 추적했습니다.
# 하지만 에이전트가 복잡해지면 print로 쫓기 어렵습니다. 이럴 때 **LangSmith** 같은 추적 도구를 붙이면
# *어느 턴에 어떤 도구를 어떤 인자로 불렀고, 토큰을 얼마 썼고, 어디서 틀렸는지* 를 자동 기록해 보여줍니다.
#
# > 💡 LangSmith는 환경변수 `LANGSMITH_TRACING=true` 와 키만 켜면 **코드를 거의 안 바꾸고** 작동합니다.
# > 우리가 print로 한 일을, 대시보드에서 턴별로 펼쳐 보여주는 셈이에요. (설정은 이 노트북 범위 밖이라 개념만.)

# ==============================================================================
# 변환본 메모
# ==============================================================================
# 1) 재고 확인: 원본 데이터에 stock 키가 없어 check_stock()은 그대로 실행하면 오류가 날 수 있습니다.
# 2) 결제 예제: 원본은 response 안의 tool_calls를 실제 TOOLS["checkout"]로 실행하는 단계가 없습니다.
# 3) 위 두 부분은 원본에 없는 값을 임의로 만들거나 로직을 덧붙이지 않기 위해 그대로 보존했습니다.
# 4) 각 PART는 앞 PART의 변수와 함수를 이어서 사용하는 구조이므로 위에서 아래 순서로 학습하는 것이 좋습니다.
