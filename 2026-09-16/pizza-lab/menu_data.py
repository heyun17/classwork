"""가게의 고정 값과 금액 계산 (2장)

메뉴 자체는 shop.db 의 menus 테이블에 있습니다 (3장).
여기에는 자주 바뀌지 않는 선택지만 둡니다.
"""

SIZES = ["R", "L"]
CRUSTS = {"기본": 0, "치즈크러스트": 3000, "고구마무스": 2000}   # 엣지 이름: 추가 금액
CHANNELS = ["배달", "포장", "매장"]
MAX_QTY = 10


def calc_amount(menu, size, crust, qty):
    """메뉴 한 개의 결제 금액 = (사이즈별 가격 + 엣지 추가금) × 수량"""
    base = menu["price_r"] if size == "R" else menu["price_l"]
    unit = base + CRUSTS[crust]
    return unit * qty
