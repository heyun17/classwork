"""기존 M2·M3 입력과 평가 정답 파일을 읽고 평가 리포트를 JSON으로 보존."""
import hashlib
import json
from pathlib import Path
from checker import load_rules,scan
from metrics import read_csv,inspect_evaluation,rank_evaluation
from search_engine import build_documents,rank_tfidf,rank_bm25

BASE=Path(__file__).resolve().parent
src=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()[:12]
files={'rules_csv':BASE/'data/rules.csv','tree_csv':BASE/'data/rule_tree.csv',
       'sample_html':BASE/'data/sample.html','detection_gold':BASE/'gold/detection_gold.csv',
       'search_gold':BASE/'gold/search_gold.csv'}
scan_results=scan(files['sample_html'].read_text(encoding='utf-8'),load_rules(files['rules_csv']))
docs=build_documents()
query_gold=read_csv(files['search_gold'])
report={
 'note':'이 파일의 정답은 교육용 검토셋이며 공식 WCAG 검사 성능 보고서가 아니다.',
 'data_sha256_prefix':{name:src(p) for name,p in files.items()},
 'document_count':len(docs),
 'inspection':inspect_evaluation(read_csv(files['detection_gold']),scan_results),
 'retrieval':{name:{f'k{k}':rank_evaluation(query_gold,engine,docs,k=k)
                 for k in (1,2,3)} for name,engine in [('tfidf',rank_tfidf),('bm25',rank_bm25)]}
}
out=BASE/'report.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('평가 결과 생성:',out.name,'/ 규칙',len(docs),'건 / 검색 질문',len(query_gold),'개')
