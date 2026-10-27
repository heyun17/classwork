"""선택 실습: rank-bm25의 BM25Okapi와 직접 구현한 양수 IDF 점수 차이 확인.
설치: python -m pip install rank-bm25
"""
from rank_bm25 import BM25Okapi

corpus=['링크 목적','링크 링크 목적','이미지 설명']
tokens=[text.split() for text in corpus]
bm25=BM25Okapi(tokens,k1=1.5,b=0.75)
for i,score in enumerate(bm25.get_scores(['링크']),start=1):
    print(f'D{i}: {score:.4f}')
print('주의: rank-bm25의 IDF 보정은 교육용 양수 IDF 공식과 다를 수 있습니다.')
