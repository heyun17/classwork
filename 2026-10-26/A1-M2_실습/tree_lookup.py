"""트리 CSV의 file + rule_id를 읽어 해당 규칙 CSV에서 정확히 찾아낸다.

python tree_lookup.py --node N_COMP_LINK_001
python tree_lookup.py --list
"""
from pathlib import Path
import argparse
import csv

BASE = Path(__file__).resolve().parent
ALLOWED_RULE_FILES = {'rules.csv'}  # CSV에서 아무 경로나 실행·읽지 않도록 제한


def read_csv(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def load_tree():
    nodes = read_csv(BASE / 'rule_tree.csv')
    by_id = {n['node_id']: n for n in nodes}
    if len(by_id) != len(nodes):
        raise ValueError('중복 node_id가 존재합니다.')
    for n in nodes:
        if n['parent_id'] and n['parent_id'] not in by_id:
            raise ValueError(f"존재하지 않는 parent_id: {n['parent_id']}")
        seen, curr = set(), n
        while curr['parent_id']:
            if curr['node_id'] in seen:
                raise ValueError('트리에서 순환 참조를 발견했습니다.')
            seen.add(curr['node_id'])
            curr = by_id[curr['parent_id']]
        if n['node_type'] == 'rule' and (not n['file'] or not n['rule_id']):
            raise ValueError('규칙 노드에는 file과 rule_id가 필수입니다.')
    return nodes, by_id


def find_rule(node_id: str):
    _, tree = load_tree()
    node = tree[node_id]
    if node['node_type'] != 'rule':
        raise ValueError('그룹이 아닌 rule 노드를 선택하세요.')
    filename = node['file']
    if filename not in ALLOWED_RULE_FILES:
        raise ValueError(f'허용되지 않은 규칙 파일: {filename}')
    rules = read_csv(BASE / filename)
    found = [r for r in rules if r['rule_id'] == node['rule_id']]
    if len(found) != 1:
        raise LookupError('file과 rule_id로 유일한 규칙을 찾지 못했습니다.')
    return node, found[0]


def print_tree():
    nodes, _ = load_tree()
    children = {}
    for node in nodes:
        children.setdefault(node['parent_id'], []).append(node)
    for group in children.values():
        group.sort(key=lambda n: int(n['sort_order']))

    def visit(parent_id, depth):
        for node in children.get(parent_id, []):
            info = f" → {node['file']} / {node['rule_id']}" if node['node_type'] == 'rule' else ''
            print('  ' * depth + f"{node['label']} [{node['node_id']}]" + info)
            visit(node['node_id'], depth + 1)
    visit('', 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', default='N_COMP_LINK_001')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    if args.list:
        print_tree()
    else:
        node, rule = find_rule(args.node)
        print('트리:', node['label'])
        print('file:', node['file'], 'rule_id:', node['rule_id'])
        print('규칙:', rule['title'])
        print('상태:', rule['status'], '/ 분류:', rule['scope'])
        print('설명:', rule['description'])
