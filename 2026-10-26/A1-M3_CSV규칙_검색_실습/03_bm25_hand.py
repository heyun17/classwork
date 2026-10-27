"""BM25: 단어 반복과 길이 정규화를 작은 수치로 계산. 양수 IDF 공식을 사용."""
from math import log
from collections import Counter
corpus=['링크 목적','링크 링크 목적','이미지 설명']
docs=[d.split() for d in corpus]
query='링크'
N=len(docs);df=sum(query in d for d in docs);avgdl=sum(map(len,docs))/N
k1=1.5;b=0.75
idf=log(1+(N-df+0.5)/(df+0.5))
print(f'N={N}, DF(링크)={df}, avgdl={avgdl:.4f}, IDF={idf:.4f}')
for i,tokens in enumerate(docs,1):
    tf=Counter(tokens)[query]
    length_factor=1-b+b*len(tokens)/avgdl
    score=idf*tf*(k1+1)/(tf+k1*length_factor) if tf else 0
    print(f'D{i}: TF={tf}, |d|={len(tokens)}, 길이보정={length_factor:.4f}, BM25={score:.4f}')
print('k1은 빈도 효과, b는 길이 보정의 정도를 조절합니다.')
