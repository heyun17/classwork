from toy_core import softmax
words=['함수','하늘','[EOS]']; logits=[2.,1.,0.]
for token,p in zip(words,softmax(logits)):
    print(token,round(p,4))
