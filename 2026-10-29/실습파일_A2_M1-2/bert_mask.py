from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline
name = "klue/bert-base"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForMaskedLM.from_pretrained(name)
print("마스크 토큰:", tok.mask_token, tok.mask_token_id)
text = "나는 오늘 점심으로 " + tok.mask_token + "를 먹었다."
ids = tok(text, return_tensors="pt")
print("입력 토큰:", tok.convert_ids_to_tokens(ids["input_ids"][0]))
print("토큰 ID:", ids["input_ids"][0].tolist())
print("다시 디코딩:", tok.decode(ids["input_ids"][0]))
fill = pipeline("fill-mask", model=model, tokenizer=tok, device=-1)
for result in fill(text, top_k=5):
    print(result["token_str"], round(result["score"], 4), result["sequence"])
