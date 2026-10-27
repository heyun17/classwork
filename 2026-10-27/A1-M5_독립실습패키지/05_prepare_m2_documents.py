"""읽기 전용 CSV -> 검색 본문/메타데이터/트리경로 생성. CSV 저장 없음."""
import argparse
import csv
from pathlib import Path
from cleaner import clean_text
DATA = Path(__file__).resolve().parent/'data'
TEXT_FIELDS = ('title','description','reason','limitation')

def load_csv(filename):
    with (DATA/filename).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def make_path(node, nodes):
    labels=[]; seen=set()
    while node:
        nid=node['node_id']
        if nid in seen: raise ValueError('트리 순환: '+nid)
        seen.add(nid);labels.append(node['label'])
        parent=node['parent_id']
        node=nodes.get(parent) if parent else None
        if parent and node is None: raise ValueError('부모 누락: '+parent)
    return ' > '.join(reversed(labels))

def build_documents(include_proposed=False):
    rules=load_csv('rules.csv'); tree=load_csv('rule_tree.csv')
    nodes={n['node_id']:n for n in tree}
    lookup={n['rule_id']:n for n in tree if n['node_type']=='rule' and n['file']=='rules.csv'}
    docs=[]
    for row in rules:
        if row['status']!='applied' and not (include_proposed and row['status']=='proposed'):
            continue
        n=lookup.get(row['rule_id'])
        if n is None: raise ValueError('트리에 없는 규칙: '+row['rule_id'])
        raw='\n'.join(f'{field}: {row[field]}' for field in TEXT_FIELDS if row.get(field))
        meta={field:value for field,value in row.items() if field not in TEXT_FIELDS}
        meta.update({'node_id':n['node_id'], 'parent_id':n['parent_id'],
                     'tree_path':make_path(n,nodes), 'preprocess_version':'nfc-ws-v1'})
        docs.append({'raw_text':raw,'clean_text':clean_text(raw),'metadata':meta})
    return docs

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-proposed',action='store_true')
    args=parser.parse_args()
    docs=build_documents(args.include_proposed)
    print('문서 수:',len(docs))
    for d in docs:
        m=d['metadata']
        print('\n',m['rule_id'], '|',m['status'],'|',m['tree_path'])
        print('검색 본문:',d['clean_text'][:150])
        print('메타데이터:',{k:m[k] for k in ('rule_version','status','reference_url','node_id','parent_id','preprocess_version')})
