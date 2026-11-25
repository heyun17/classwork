import difflib
a = "솔바람섬 별빛 2박3일은 바람길여행이 판매하는 투어 상품으로 가격은 1인 39만 원 (VAT 포함 &amp; 유류할증료 별도)이다.  <br>  숙소는 파도소리 리조트 2박이 포함된다."
b = "솔바람섬 별빛 2박3일은 바람길여행이 판매하는 투어 상품으로 가격은 1인 39만 원 (VAT 포함 &amp; 유류할증료 별도)이다. 숙소는 파도소리 리조트 2박이 포함된다."
for line in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0):
    print(line)