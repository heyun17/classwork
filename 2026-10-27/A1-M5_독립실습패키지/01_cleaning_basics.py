import unicodedata
from cleaner import clean_text
raw = '  WCAG 2.4.4\n\n aria-label\t  접근성이 좋지 않습니다  '
result = clean_text(raw)
print('원본:',repr(raw))
print('정제:',repr(result))
for word in ['WCAG 2.4.4', 'aria-label', '좋지 않습니다']:
    print('보존:', word, word in result)
    assert word in result
sample='① Ａ ㍿'
print('NFC :',unicodedata.normalize('NFC',sample))
print('NFKC:',unicodedata.normalize('NFKC',sample))
assert unicodedata.normalize('NFC','①') != unicodedata.normalize('NFKC','①')
print('해설: NFKC는 호환 문자(예: ①)를 일반 표현(1)로 바꿀 수 있다.')
