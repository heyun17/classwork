"""M2 기존 검사기 코드를 수정하지 않고 검토 정답과 비교."""
from pathlib import Path
from checker import load_rules, scan
from metrics import read_csv, inspect_evaluation

BASE=Path(__file__).resolve().parent
rules=load_rules(BASE/'data/rules.csv')
html=(BASE/'data/sample.html').read_text(encoding='utf-8')
findings=scan(html,rules)
gold=read_csv(BASE/'gold/detection_gold.csv')
result=inspect_evaluation(gold,findings)
print('적용 규칙:',len(rules),' / 검사 결과:',len(findings))
print('검토 정답:',result['labeled_total'],' / 일치율:',round(100*result['exact_agreement'],2),'%')
print('정답 기준 판단 보류:',result['review_expected'],
      '/ 실제 판단 보류:',result['review_predicted'])
print('이진 지표 대상:',result['binary_scored'],' / coverage:',
      round(100*result['decision_coverage'],2),'%')
print('이진 지표:',result['binary'])
print('※ 교육용 샘플에 맞춰 만든 검토 정답으로 현장 성능이 입증된 것은 아닙니다.')
