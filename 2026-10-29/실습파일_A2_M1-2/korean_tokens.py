from transformers import AutoTokenizer
for name in ["klue/bert-base", "skt/kogpt2-base-v2"]:
    tok = AutoTokenizer.from_pretrained(name)
    print(name, tok.special_tokens_map)
    text = "메타정합검증 WCAG 2.4.4"
    enc = tok(text)
    print(tok.convert_ids_to_tokens(enc["input_ids"]))
    print(enc["input_ids"], tok.decode(enc["input_ids"], skip_special_tokens=True))
