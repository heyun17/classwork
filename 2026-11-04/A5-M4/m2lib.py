"""A5-M2 실습 공통 코드 — OpenAI API로 정책 문서에서 개체·관계·속성을 뽑는다.

- API 키와 모델은 .env에서 읽는다 (OPENAI_API_KEY, OPENAI_MODEL).
- 호출 결과(보낸 프롬프트, 받은 응답, 토큰 수)는 outputs_m2/raw/에 파일로 저장한다.
  같은 이름의 결과가 있으면 다시 호출하지 않고 파일을 읽는다 (--refresh로 새로 호출).
- --dry-run이면 API를 부르지 않고 보낼 프롬프트만 보여 준다.
"""
import json
import os
import time
from pathlib import Path

from m1lib import load_policies, normalize  # noqa: F401  (M1에서 만든 로더를 그대로 쓴다)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs_m2"
RAW = OUT / "raw"


def load_env(path=ROOT / ".env"):
    """간단한 .env 읽기: KEY=VALUE 줄만. 이미 설정된 환경변수는 덮어쓰지 않는다."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


load_env()
MODEL = os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"


def ask_json(name, system, user, dry_run=False, refresh=False):
    """OpenAI에 JSON 응답을 요청하고, 요청과 응답을 outputs_m2/raw/<name>.json에 저장한다."""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{name}.json"
    if dry_run:
        print(f"[dry-run] {name} · 모델 {MODEL}\n--- system ---\n{system}\n--- user ---\n{user}\n")
        return None
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    from openai import OpenAI  # pip install openai

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    kwargs = {"model": MODEL, "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if MODEL.startswith("gpt-4"):
        kwargs["temperature"] = 0  # 같은 입력에 같은 답이 나오도록
    t0 = time.time()
    resp = client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content
    record = {"name": name, "model": resp.model, "seconds": round(time.time() - t0, 1),
              "usage": {"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens},
              "system": system, "user": user, "response_text": text, "data": json.loads(text)}
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def policy(doc_id):
    return next(d for d in load_policies() if d["id"] == doc_id)


# ------------------------------------------------------------------ 프롬프트
SYSTEM = ("너는 쇼핑몰 정책 문서에서 지식을 뽑아 정리하는 도우미다. "
          "문서에 적힌 내용만 쓰고, 추측하지 않는다. 반드시 JSON 하나로만 답한다.")

FREE_FORMAT = """다음 정책 문서에서 개체(entity), 관계(triple), 속성(property)을 뽑아라.

- entities: 문서에 나오는 중요한 '것'과 그 종류. 예) {"name": "냉장식품", "type": "상품유형"}
- triples : (주어, 관계, 목적어). evidence에는 근거가 된 문장을 문서에서 그대로 옮긴다.
- properties: 어떤 개체가 갖는 값(기한, 금액 등). evidence에는 근거 문장을 그대로 옮긴다.

JSON 형식:
{"entities": [{"name": "", "type": ""}],
 "triples": [{"subject": "", "predicate": "", "object": "", "evidence": ""}],
 "properties": [{"entity": "", "name": "", "value": "", "evidence": ""}]}

문서 ID: {doc_id}
문서:
{text}"""


def free_prompt(doc):
    return FREE_FORMAT.replace("{doc_id}", doc["id"]).replace("{text}", normalize(doc["text"]))


def schema_prompt(doc, schema):
    """설계한 스키마(개체 종류, 이름 목록, 관계 목록)를 알려 주고 그 안에서만 뽑게 한다."""
    types = "\n".join(f"- {t}: {', '.join(v['names']) if v.get('names') else v['desc']}" for t, v in schema["entity_types"].items())
    preds = "\n".join(f"- {p['name']}: {p['subject']} → {p['object']} · {p['desc']}" for p in schema["predicates"])
    pols = ""
    if any(v.get("list_policies") for v in schema["entity_types"].values()):
        pols = "\n[정책 목록]\n" + "\n".join(f"- {d['id']}: {d['title']}" for d in load_policies()) + "\n"
    extra = "".join(f"\n- {r}" for r in schema.get("rules", []))
    ex = schema.get("example")
    if ex:  # 예시 문서 하나로 맞는 트리플과 틀린 트리플을 보여 준다 (few-shot)
        good = "\n".join(f"  ({s}, {p}, {o})" for s, p, o in ex["good"])
        bad = "\n".join(f"  ({s}, {p}, {o})  ✗ {why}" for s, p, o, why in ex["bad"])
        pols += f"\n[예시] 문서 {ex['doc_id']}: {ex['text']}\n맞는 트리플:\n{good}\n틀린 트리플:\n{bad}\n"
    return f"""다음 정책 문서에서 관계(triple)와 속성(property)을 뽑아라. 아래 규칙을 반드시 지킨다.

[개체 종류와 이름] 이름이 정해진 종류는 반드시 그 이름 중 하나로 쓴다.
{types}

[관계 이름] 아래 관계 이름만 쓴다. 맞는 관계가 없으면 뽑지 않는다.
{preds}
{pols}
[규칙]
- 이 문서 자체는 subject를 "{doc['id']}"로 쓴다.
- evidence에는 근거 문장을 문서에서 그대로 옮긴다.
- properties의 name은 기한, 금액, 기간 중 하나다.{extra}

JSON 형식:
{{"triples": [{{"subject": "", "subject_type": "", "predicate": "", "object": "", "object_type": "", "evidence": ""}}],
 "properties": [{{"entity": "", "name": "", "value": "", "evidence": ""}}]}}

문서 ID: {doc['id']}
문서:
{normalize(doc['text'])}"""
