"""A2-M2: 하나의 E5 인코더를 활용하는 공통 코드. 실행 시 최초 모델 다운로드가 필요하다."""
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

MODEL_ID = "intfloat/multilingual-e5-small"


def load():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    model = AutoModel.from_pretrained(MODEL_ID)
    model.eval()
    return tokenizer, model


def mean_pool(last_hidden_state, attention_mask):
    mask = attention_mask.unsqueeze(-1).to(last_hidden_state.dtype)
    summed = (last_hidden_state * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1)
    return summed / counts


@torch.inference_mode()
def embed(texts, tokenizer, model, kind="passage", max_length=256):
    if kind not in ("query", "passage"):
        raise ValueError("kind는 query 또는 passage")
    prefixed = [f"{kind}: {text}" for text in texts]
    encoded = tokenizer(prefixed, padding=True, truncation=True,
                        max_length=max_length, return_tensors="pt")
    result = model(**encoded)
    pooled = mean_pool(result.last_hidden_state, encoded["attention_mask"])
    return F.normalize(pooled, p=2, dim=1)
