"""터미널에서 AI 호출 연습 (4장)

실행: python ai_test.py
"""
from ai import MODEL, ask, has_key

if not has_key():
    raise SystemExit("❌ .env 에 OPENAI_API_KEY 가 없습니다. 1장을 확인하세요.")

print("모델:", MODEL)

# ① 가장 단순한 질문
print("\n[1] 한 줄 자랑")
print(ask("페퍼로니 피자를 한 문장으로 자랑해줘."))

# ② 데이터를 끼워 넣은 질문 (f-string)
menu, sold, rank = "하와이안", 12, 6
print("\n[2] 데이터 넣어서 묻기")
question = (f"{menu} 피자가 이번 주 {sold}판 팔려 6개 메뉴 중 {rank}위야. "
            "살릴 아이디어 2개만.")
print(ask(question))

# ③ 역할 지시를 바꿔서 묻기
print("\n[3] 말투 바꾸기")
print(ask("오늘 비가 와. 배달 손님을 늘릴 방법 하나.",
          system="너는 사투리를 쓰는 유쾌한 피자집 매니저다."))
