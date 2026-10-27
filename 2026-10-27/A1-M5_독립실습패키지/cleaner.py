"""A1-M5 검색 전처리만 수행. 규칙 원본/상태/ID는 절대 변경하지 않는다."""
import re
import unicodedata

def clean_text(text):
    text = unicodedata.normalize('NFC', text)
    return re.sub(r'\s+', ' ', text).strip()

def whitespace_tokens(text):
    return text.split()

def char_ngrams(text, n=2):
    chars = ''.join(text.split())
    return [chars[i:i+n] for i in range(max(0, len(chars)-n+1))]
