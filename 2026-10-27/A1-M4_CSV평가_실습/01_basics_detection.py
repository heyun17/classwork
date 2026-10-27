"""A1-M4-02: 손으로 계산한 TP=4 FP=2 FN=1 TN=3 수치 확인."""
from metrics import binary_scores
truth=[1]*5+[0]*5
prediction=[1,1,1,1,0,1,1,0,0,0]
s=binary_scores(truth,prediction)
print('혼동행렬: TP=',s.tp,'FP=',s.fp,'FN=',s.fn,'TN=',s.tn)
print(f'Precision={s.precision:.4f}  Recall={s.recall:.4f}  F1={s.f1:.4f}')
print(f'Accuracy={s.accuracy:.4f}')
