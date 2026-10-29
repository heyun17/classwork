from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, set_seed
name = "skt/kogpt2-base-v2"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name)
set_seed(42)
prompt = "나는 오늘 점심으로"
ids = tok(prompt)["input_ids"]
print("토큰:", tok.convert_ids_to_tokens(ids))
print("ID:", ids)
print("복원:", tok.decode(ids))
print("pad / eos:", tok.pad_token_id, tok.eos_token_id)
gen = pipeline("text-generation", model=model, tokenizer=tok, device=-1)
result = gen(prompt, do_sample=False, max_new_tokens=30,
             pad_token_id=tok.eos_token_id)
print(result[0]["generated_text"])
