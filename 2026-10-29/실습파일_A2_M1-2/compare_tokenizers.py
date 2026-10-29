from transformers import AutoTokenizer
samples = ["나는 오늘 점심으로 피자를 먹었다.", "파이썬으로 RAG 검색을 구현합니다."]
names = ["klue/bert-base", "skt/kogpt2-base-v2"]
for name in names:
    tok = AutoTokenizer.from_pretrained(name)
    print("\n모델:", name, "어휘 크기:", tok.vocab_size)
    for sent in samples:
        ids = tok(sent)["input_ids"]
        print("문장:",sent)
        print("토큰:",tok.convert_ids_to_tokens(ids))
        print("개수:",len(ids), "복원:",tok.decode(ids, skip_special_tokens=True))
