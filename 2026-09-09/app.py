import re

# 원본 텍스트 입력
text = input("문장을 입력하세요: ")

# 1. 전체 글자 수
total_count = len(text)

# 2. 한글만 남기기
korean_text = ''.join(re.findall(r'[가-힣ㄱ-ㅎㅏ-ㅣ]', text))

# 3. 한글 글자 수
korean_count = len(korean_text)

# 4. 전체 글자 중 한글 비율 계산
if total_count > 0:
    korean_ratio = (korean_count / total_count) * 100
else:
    korean_ratio = 0

# 결과 출력
print()
print("원본:", text)
print("전체 글자 수:", total_count)
print("한글만:", korean_text)
print("한글 글자 수:", korean_count)
print(f"한글 비율: {korean_ratio:.2f}%")