"""M3 기존 TF-IDF/BM25 검색 엔진에서 실제 순위를 얻어 평가."""
from pathlib import Path
from metrics import read_csv,rank_evaluation
from search_engine import build_documents,rank_tfidf,rank_bm25

BASE=Path(__file__).resolve().parent
docs=build_documents()
gold=read_csv(BASE/'gold/search_gold.csv')
print('검색 대상 적용 규칙:',len(docs),'건 / proposed 기본 제외')
for name,engine in [('TF-IDF',rank_tfidf),('BM25',rank_bm25)]:
    for k in (1,2,3):
        report=rank_evaluation(gold,engine,docs,k=k)
        m=report['macro']
        print(f'{name:6} k={k} Recall@k={m["recall"]:.3f}, Hit@k={m["hit"]:.3f}, '
              f'MRR@k={m["rr"]:.3f}, nDCG@k={m["ndcg"]:.3f}')
    q2=next(row for row in report['rows'] if row['qid']=='Q02')
    print(name,'Q02 top3:',q2['topk'],' / 정답:',q2['relevant'])
print('※ 알고리즘별 원시 점수 크기를 서로 비교하지 않고 순위를 평가합니다.')
