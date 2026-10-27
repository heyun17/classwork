"""BoW는 문서를 단어 출현 횟수 벡터로 바꾼다. 표와 출력 순서는 단어 사전 정렬 순서다."""
from collections import Counter
corpus = ['이미지 대체 텍스트','이미지 설명','링크 목적']
tokens = [s.split() for s in corpus]
vocab = sorted({w for words in tokens for w in words})
print('어휘 목록:',vocab)
rows=[]
for i,words in enumerate(tokens,1):
    counts=Counter(words)
    vector=[counts[w] for w in vocab]
    print(f'D{i}:', vector)
    rows.append(vector)
try:
    import pandas as pd
    print('\n단어별 출현 횟수 표')
    print(pd.DataFrame(rows,columns=vocab,index=['D1','D2','D3']).to_string())
except ImportError:
    print('(pandas 미설치: 위 벡터 출력만 사용해도 됩니다.)')
