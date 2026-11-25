# 미션 1 · LLM을 부르기 전에 '문서 범위 밖' 질문 걸러내기
# 1) 아래 코드를 src/s09_answer.py 의 retrieve 함수 바로 위에 붙여 넣습니다.
# 2) run() 안의 call_llm(...) 줄을 교안 12탭 정답처럼 바꿔, pre_check가 이유를 돌려주면 LLM을 부르지 않게 합니다.
# 3) s09 → s10 → s11 실행. 완료 기준: N01·N02·N03 보류, 답변 가능한 20개 중 보류 0개
import re as _re
from common import load_metadata

_META = load_metadata()
KNOWN_YEARS = {m["year"] for m in _META}
KNOWN_REGIONS = {m["region"] for m in _META}
KNOWN_CODES = {m["product_code"] for m in _META if m["product_code"]}
OTHER_REGIONS = ["인천", "대구", "울산", "세종", "제주", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남"]


def pre_check(question):
    """걸리면 이유 문자열, 아니면 None"""
    for y in _re.findall(r"(20\d\d)", question):
        if int(y) not in ____________:
            return f"없는 연도 {y}"
    for r in OTHER_REGIONS:
        if r in question:
            return f"없는 지역 {r}"
    for c in _re.findall(r"[A-Z]{2,}-[A-Z]+-\d{2}", question):
        if c not in ____________:
            return f"없는 제품코드 {c}"
    return None
