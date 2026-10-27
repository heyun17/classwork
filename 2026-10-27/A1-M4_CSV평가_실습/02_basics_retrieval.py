"""A1-M4-03: 관련 문서 3개 중 Top-3에서 2개 검색된 경우."""
from metrics import retrieval_scores
relevant={'IMG-001','LINK-002','COMP-LINK-001'}
ranked=['FORM-001','IMG-001','LINK-002','COMP-LINK-001']
for k in (1,2,3,4):
    m=retrieval_scores(relevant,ranked,k)
    print(f'k={k} Recall@k={m["recall"]:.4f} Hit@k={m["hit"]:.4f} '
          f'RR@k={m["rr"]:.4f} nDCG@k={m["ndcg"]:.4f}')
