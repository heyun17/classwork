from toy_core import encode, causal_visibility
_,ids,mask=encode('파이썬 좋아')
print('input_ids:',ids,'padding_mask:',mask)
for i,row in enumerate(causal_visibility(len(ids))):
    both=[int(bool(c and p)) for c,p in zip(row,mask)]
    print('query',i,'causal',row,'결합',both,'query_valid',mask[i])
