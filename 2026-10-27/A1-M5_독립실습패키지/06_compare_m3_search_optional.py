"""M3의 문자 n-gram TF-IDF 설정으로 원문/정제본 검색 순위를 비교한다.
M3 검색 엔진 자체를 덮어쓰지 않는 독립 비교 실습이다.
"""
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    raise SystemExit('먼저 python -m pip install scikit-learn 를 실행하세요.')
from cleaner import clean_text
from importlib import import_module
build_documents=import_module('05_prepare_m2_documents').build_documents
docs=build_documents()
queries=['aria-label 링크 이름','이미지 alt 속성','사내 더보기 문구 제한']
for query in queries:
    print('\n질문:',query)
    for label, corpus in [('원문',[d['raw_text'] for d in docs]),('정제',[d['clean_text'] for d in docs])]:
        model=TfidfVectorizer(analyzer='char',ngram_range=(2,4))
        matrix=model.fit_transform(corpus)
        scores=cosine_similarity(model.transform([clean_text(query)]),matrix)[0]
        rank=sorted(range(len(scores)),key=lambda i:(-scores[i],i))[:3]
        print(label,[(docs[i]['metadata']['rule_id'],round(float(scores[i]),4)) for i in rank])
print('\n순위가 같아도 정상입니다. 실제 개선 여부는 M4 정답셋으로 별도 평가해야 합니다.')
