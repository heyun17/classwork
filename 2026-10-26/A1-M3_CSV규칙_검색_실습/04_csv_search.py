"""M2 CSV를 그대로 검색: 문자열 점수와 CSV 메타데이터·트리 위치를 함께 출력."""
from search_engine import build_documents, rank_tfidf,rank_bm25,lookup_by_tree_node

records=build_documents() # status=applied, proposed 기본 제외
query='더보기 링크 목적이 모호한 경우'
print('질의:',query,'/ 적용 문서:',len(records))
for method in (rank_tfidf,rank_bm25):
    print('\n검색 방식:',method.__name__)
    for doc,score in method(query,records,top_k=3):
        m=doc.metadata
        print(f'{doc.document_id:<16} score={score:.4f} scope={m["scope"]} status={m["status"]}')
        print('  트리:',m['tree_path'] or '트리 미연결')
        print('  출처:',f'{m["source_file"]}:{m["rule_id"]}',m['reference_url'])

print('\n트리 노드 → 원본 규칙 행 찾기')
doc=lookup_by_tree_node('N_COMP_LINK_001')
print(doc.document_id,doc.text)
print('메타데이터:',doc.metadata)
print('\n제안 규칙 포함하면:',len(build_documents(include_proposed=True)),'건 (현재 정책과 구분해서 사용)')
