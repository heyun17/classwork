"""TF-IDF: scikit-learn 공식 기본 평활 IDF를 숫자로 검산하고 코사인 유사도를 구한다."""
from math import log
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

corpus=['이미지 대체 텍스트','이미지 설명','링크 목적']
query='이미지 대체'
model=TfidfVectorizer(tokenizer=str.split,token_pattern=None,lowercase=False,
                      norm='l2',smooth_idf=True)
X=model.fit_transform(corpus)
q=model.transform([query]) # fit을 다시 하면 문서·질의의 단어 좌표계가 달라짐
terms=model.get_feature_names_out()
print('용어, df, idf')
for term,idf in zip(terms,model.idf_):
    df=sum(term in d.split() for d in corpus)
    manual=log((len(corpus)+1)/(df+1))+1
    print(f'{term:8} df={df}, IDF={idf:.4f} (직접 계산 {manual:.4f})')
print('\nTF-IDF 벡터 (행=문서, 열=단어)')
try:
    import pandas as pd
    print(pd.DataFrame(X.toarray(),columns=terms,index=['D1','D2','D3']).round(3).to_string())
except ImportError:
    for i,row in enumerate(X.toarray(),1):print(f'D{i}:',[round(float(v),3) for v in row])
print('\n질의와의 코사인 유사도')
for i,score in enumerate(cosine_similarity(q,X)[0],1):
    print(f'D{i}: {score:.4f}')
