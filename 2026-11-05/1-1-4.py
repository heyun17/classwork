import html, re
page = """<div class=\"post\">\n<h2>🏝️ 별빛전망대</h2>\n<p>별빛전망대는 솔바람섬 북쪽 언덕 꼭대기에 있는 천문 관측 명소이다. 맑은 날 밤에는 은하수를 맨눈으로 볼 수 있다.</p>\n<p>별빛전망대는 매주 월요일에 휴관하며 입장료는 5천 원이다. 전망대까지는 섬 선착장에서 걸어서 약 30분이 걸린다.</p>\n<p>겨울철에는 오후 9시에 문을 닫는다.</p>\n<div class=\"footer\">▶ 공유하기 &nbsp;|&nbsp; ★ 즐겨찾기 &nbsp;|&nbsp; 문의: tour@eunha.example</div>\n</div>"""

title = re.search(r"<h2>(.*?)</h2>", page, re.S).group(1)
title = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", title).strip()

t = re.sub(r"<h2>.*?</h2>", " ", page, flags=re.S)
t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)  # 수정
t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
t = re.sub(r'<div class="footer">.*?</div>', " ", t, flags=re.S)
t = re.sub(r"<[^>]+>", " ", t)
t = re.sub(r"[★☆▶◀■□●○◆◇♥]", "", t)                              # 장식 기호
t = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", t)  # 이모지
t = re.sub(r"\s+", " ", t).strip()

print(f"<{title}>", t)
