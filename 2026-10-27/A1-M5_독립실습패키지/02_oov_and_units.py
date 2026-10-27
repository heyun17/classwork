from cleaner import whitespace_tokens, char_ngrams
vocab = {'규칙','검사','링크','이름','배송','빠르다'}
text='메타정합검증 규칙 검사'
print('어휘 목록:',sorted(vocab))
for term in whitespace_tokens(text):
    print(repr(term), '등록' if term in vocab else 'OOV(미등록 어휘)')
print('공백 분할:',whitespace_tokens(text))
print('문자 2-gram:',char_ngrams(text,2))
print('주의: 이 코드는 실제 LLM 토큰화나 토큰 ID를 생성하지 않습니다.')
