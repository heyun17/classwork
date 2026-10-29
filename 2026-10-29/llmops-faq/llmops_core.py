# LLMOps 따라하기 — 쇼핑몰 FAQ 챗봇 (배포 제외, 로컬에서 실제 LLMOps 순환 구현)
# 이 파일은 01_따라하기.ipynb의 코드 셀을 그대로 모은 것이다.
# watch.py와 02_실습과제.ipynb가 이 파일을 불러다 쓴다.

# %% [1] 프로젝트 폴더와 설정
import os, re, csv, json, time, uuid, hashlib, datetime, unicodedata
from pathlib import Path
import numpy as np

def set_project(root="."):
    """실습 폴더 위치를 정하고 하위 폴더를 만든다."""
    global ROOT, DATA, ART, LOGS, FAQ_FILE, EVAL_FILE, SYN_FILE, REGISTRY_FILE
    ROOT = Path(root)
    DATA, ART, LOGS = ROOT / "data", ROOT / "artifacts", ROOT / "logs"
    FAQ_FILE = DATA / "faq.csv"                 # 운영자가 고치는 FAQ
    SYN_FILE = DATA / "synonyms.csv"            # 분야별 동의어 사전
    EVAL_FILE = DATA / "eval_set.jsonl"         # 평가셋 (라벨링 결과가 쌓인다)
    REGISTRY_FILE = ROOT / "registry.json"      # 버전 기록 + 현재 활성 버전
    for d in (DATA, ART, LOGS):
        d.mkdir(parents=True, exist_ok=True)

set_project(".")

CONFIG = {                       # 이 값이 바뀌어도 파이프라인이 다시 돈다
    "use_bert": True,
    "embed_model": "klue/bert-base",
    "alpha": 0.5,                # TF-IDF 비중 (1-alpha = BERT 비중)
    "top_k": 3,
    "min_score": 0.05,
    "prompt_version": "faq-v1",
    "use_llm": True,             # False면 GPT 대신 mock (비용 0, 결과 재현용)
    "llm_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "temperature": 0.2,
}
GATE = {"hit1": 0.80, "cite_rate": 0.80, "max_new_fail": 0}   # 활성화 기준
ALERT = {"no_hit_rate": 0.10, "bad_feedback_rate": 0.20, "p95_latency_ms": 3000}

# 실습 과제에서 기능을 끼워 넣는 자리 (함수를 리스트/딕셔너리에 추가하면 된다)
CUSTOM_CHECKS = []    # fn(docs, evals) -> [오류 메시지]
CUSTOM_GATES = []     # fn(result) -> (통과 여부, 메시지)
CUSTOM_METRICS = {}   # 이름 -> fn(logs, feedbacks) -> 값

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

def append_jsonl(path, rec):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# %% [2] 처음 데이터 만들기 — FAQ · 동의어 사전 · 평가셋
SEED_FAQ = [
    ("D1", "배송은 언제 오나요?", "주문 후 평일 기준 2~3일 이내에 배송이 도착합니다. 제주·도서산간 지역은 3~5일이 걸립니다."),
    ("D2", "배송비는 얼마인가요?", "30000원 이상 구매 시 무료 배송이며, 미만이면 배송비 3000원이 부과됩니다."),
    ("D3", "교환·반품은 언제까지 되나요?", "상품을 수령한 날부터 7일 이내에 교환 또는 반품을 신청할 수 있습니다."),
    ("D4", "반품 배송비는 누가 내나요?", "단순 변심으로 반품하면 왕복 배송비 6000원을 고객이 부담합니다. 상품 불량은 무료입니다."),
    ("D5", "환불은 언제 되나요?", "반품 상품이 확인되면 3영업일 이내에 환불됩니다. 카드 결제 취소는 카드사에 따라 3~7일이 더 걸릴 수 있습니다."),
    ("D6", "주문을 취소하고 싶어요", "배송 준비 전이라면 마이페이지 주문 내역에서 직접 취소할 수 있습니다."),
    ("D7", "대형 상품은 어떻게 배송되나요?", "냉장고·소파처럼 무게 30kg 이상이거나 가로 150cm 이상인 상품은 화물로 배송되며 설치 일정은 전화로 협의합니다."),
    ("D8", "적립금은 언제 소멸되나요?", "구매 금액의 1%가 적립금으로 쌓이며 유효기간은 적립일로부터 1년입니다."),
]
SEED_SYNONYMS = [   # (찾을 말 — 정규식, 바꿀 말, 설명)
    ("택배비|배달비", "배송비", "동의어"),
    ("택배로|배달로", "배송으로", "조사까지 함께 바꿔 '배송로'가 되지 않게"),
    ("택배|배달", "배송", "동의어"),
    ("리턴", "반품", "동의어"),
    ("캔슬", "취소", "동의어"),
    ("무배", "무료 배송", "줄임말"),
    ("포인트", "적립금", "동의어"),
    ("사라지|사라져|없어지|없어져", "소멸", "동의어"),
    ("일주일", "7일", "기간 표기"),
]
SEED_EVAL = [
    ("택배 언제 와요?", "D1"), ("2만 원어치 사면 배송비 얼마예요?", "D2"),
    ("받은 지 5일 됐는데 리턴 되나요?", "D3"), ("단순 변심이면 반품 택배비 내야 해요?", "D4"),
    ("환불은 며칠 걸려요?", "D5"), ("주문 캔슬하고 싶어요", "D6"),
    ("35키로 냉장고도 일반 택배로 와요?", "D7"), ("포인트는 언제 사라져요?", "D8"),
]

def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:   # utf-8-sig: 엑셀에서 열어도 한글이 안 깨진다
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def init_project(reset=False):
    """처음 한 번 실행. reset=True면 데이터·버전·로그를 모두 처음 상태로 되돌린다."""
    if reset:
        for p in [REGISTRY_FILE, *LOGS.glob("*.jsonl")]:
            p.unlink(missing_ok=True)
        for d in ART.glob("v*"):
            for f in d.iterdir():
                f.unlink()
            d.rmdir()
    if reset or not FAQ_FILE.exists():
        write_csv(FAQ_FILE, ["id", "title", "text"], SEED_FAQ)
    if reset or not SYN_FILE.exists():
        write_csv(SYN_FILE, ["pattern", "replace", "note"], SEED_SYNONYMS)
    if reset or not EVAL_FILE.exists():
        EVAL_FILE.write_text("".join(json.dumps({"q": q, "gold": g, "source": "초기"}, ensure_ascii=False) + "\n"
                                     for q, g in SEED_EVAL), encoding="utf-8")
    print("data/ 준비 완료:", [p.name for p in sorted(DATA.iterdir())])


# %% [3] 데이터 정제 — 개인정보 → 공통 → 단위 → 동의어 사전(파일)
def _won(m, mult):
    return f"{int(float(m.group(1)) * mult)}원"

PRIVACY_RULES = [
    (r"\d{6}-?[1-4]\d{6}", "[주민번호]", "개인정보 마스킹"),
    (r"01[016789]-?\d{3,4}-?\d{4}", "[전화번호]", "개인정보 마스킹"),
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "[이메일]", "개인정보 마스킹"),
]
COMMON_RULES = [
    (r"<[^>]+>", " ", "HTML 태그 제거"),
    (r"([!?.])\1+", r"\1", "반복 문장부호 축약"),
    (r"(?<=\d),(?=\d{3}(?!\d))", "", "천 단위 쉼표 제거"),
]
UNIT_RULES = [   # 순서 중요: kg을 km보다 먼저, mm·cm를 m보다 먼저
    (r"(\d+(?:\.\d+)?)\s*만\s*원", lambda m: _won(m, 10000), "금액 → 숫자(만원)"),
    (r"(\d+(?:\.\d+)?)\s*천\s*원", lambda m: _won(m, 1000), "금액 → 숫자(천원)"),
    (r"(\d+)\s+원", r"\1원", "금액 띄어쓰기"),
    (r"(\d+(?:\.\d+)?)\s*(?:킬로그램|키로그램|kg|KG|Kg)", r"\1kg", "kg 단위 통일"),
    (r"(\d+(?:\.\d+)?)\s*(?:킬로미터|키로미터|km|KM|Km)", r"\1km", "km 단위 통일"),
    (r"(\d+(?:\.\d+)?)\s*(?:킬로|키로)", r"\1kg", "킬로(무게) → kg"),
    (r"(\d+(?:\.\d+)?)\s*(?:밀리미터|미리|mm|MM)(?![A-Za-z])", r"\1mm", "mm 단위 통일"),
    (r"(\d+(?:\.\d+)?)\s*(?:센티미터|센티|센치|cm|CM)(?![A-Za-z])", r"\1cm", "cm 단위 통일"),
    (r"(\d+(?:\.\d+)?)\s*(?:미터)", r"\1m", "m 단위 통일"),
    (r"(\d+(?:\.\d+)?)\s*(?:밀리그램|mg|MG)(?![A-Za-z/])", r"\1mg", "mg 단위 통일"),
    (r"(\d+(?:\.\d+)?)\s*(?:°\s?C|도씨)", r"\1°C", "°C 단위 통일"),
]

def load_synonyms(path=None):
    return [(r["pattern"], r["replace"], r.get("note", "")) for r in read_csv(path or SYN_FILE)]

def mask_pii(text):
    for pat, rep, _ in PRIVACY_RULES:
        text = re.sub(pat, rep, text)
    return text

def clean_text(text, synonyms=(), log=None):
    s = unicodedata.normalize("NFKC", text)             # ３만→3만, ㎏→kg, ℃→°C
    if log is not None and s != text:
        log.append(("유니코드 정규화(NFKC)", 1))
    rules = PRIVACY_RULES + COMMON_RULES + UNIT_RULES + [(p, r, f"사전: {n or p}") for p, r, n in synonyms]
    for pat, rep, name in rules:
        s, n = re.subn(pat, rep, s)
        if n and log is not None:
            log.append((name, n))
    return re.sub(r"\s+", " ", s).strip()


# %% [4] Kiwi 형태소 분석
from kiwipiepy import Kiwi
kiwi = Kiwi()
KEEP = {"NNG", "NNP", "VV", "VA", "XR", "SL", "SN"}   # 명사·동사·형용사·어근·외국어·숫자
STOP = {"있", "하", "되", "수"}                         # 어디에나 나와 검색을 흐리는 말

def tokenize_ko(text):
    return [t.form for t in kiwi.tokenize(text) if t.tag in KEEP and t.form not in STOP]


# %% [5] 색인 — TF-IDF + 허깅페이스 BERT 임베딩, 버전 폴더에 저장·불러오기
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_bert = {}
def load_bert(name):
    """허깅페이스 토크나이저 + BERT를 불러와 문장 → 768차원 벡터 함수를 돌려준다."""
    if name not in _bert:
        import torch
        from transformers import AutoTokenizer, AutoModel
        tok = AutoTokenizer.from_pretrained(name)
        mdl = AutoModel.from_pretrained(name).eval()
        def embed(texts):
            enc = tok(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
            with torch.no_grad():
                out = mdl(**enc)
            mask = enc["attention_mask"].unsqueeze(-1).float()
            return ((out.last_hidden_state * mask).sum(1) / mask.sum(1)).numpy()   # 평균 풀링
        _bert[name] = embed
    return _bert[name]

def get_embedder(cfg):
    if not cfg["use_bert"]:
        return None
    try:
        return load_bert(cfg["embed_model"])
    except Exception as e:
        if "_warned" not in _bert:
            print(f"   (BERT 사용 불가: {type(e).__name__} → TF-IDF만 사용)")
            _bert["_warned"] = True
        return None

def make_index(docs, synonyms, cfg, emb=None):
    corpus = [clean_text(d["title"] + " " + d["text"], synonyms) for d in docs]
    vec = TfidfVectorizer(tokenizer=tokenize_ko, token_pattern=None, lowercase=False)
    X = vec.fit_transform(corpus)
    embed = get_embedder(cfg)
    if embed is not None and emb is None:
        emb = embed(corpus)
    return {"docs": docs, "synonyms": synonyms, "corpus": corpus, "vec": vec, "X": X,
            "embed": embed if emb is not None else None, "emb": emb}

def save_index(version, idx, manifest):
    d = ART / version
    d.mkdir(parents=True, exist_ok=True)
    (d / "docs.json").write_text(json.dumps({"docs": idx["docs"], "synonyms": idx["synonyms"]},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
    if idx["emb"] is not None:
        np.save(d / "emb.npy", idx["emb"])
    (d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

def load_index(version, cfg):
    d = ART / version
    saved = json.loads((d / "docs.json").read_text(encoding="utf-8"))
    emb = np.load(d / "emb.npy") if (d / "emb.npy").exists() else None
    return make_index(saved["docs"], [tuple(s) for s in saved["synonyms"]], cfg, emb=emb)


# %% [6] 코사인 유사도 검색 (하이브리드)
def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def minmax(x):
    return (x - x.min()) / (x.max() - x.min() + 1e-9)

def search(q, idx, cfg):
    qc = clean_text(q, idx["synonyms"])
    t = cosine_similarity(idx["vec"].transform([qc]), idx["X"])[0]
    if idx["embed"] is not None:
        qv = idx["embed"]([qc])[0]
        b = np.array([cosine(qv, v) for v in idx["emb"]])
        score = cfg["alpha"] * minmax(t) + (1 - cfg["alpha"]) * minmax(b)
    else:
        score = t
    top = np.argsort(-score)[:cfg["top_k"]]
    return [{"id": idx["docs"][i]["id"], "i": int(i), "score": round(float(score[i]), 3)}
            for i in top if score[i] >= cfg["min_score"]]


# %% [7] 생성 — 프롬프트 + GPT API (키가 없거나 장애면 mock)
try:
    from dotenv import load_dotenv
    load_dotenv(".env")                     # 실습 폴더의 .env → OPENAI_API_KEY
except ImportError:
    pass

PROMPTS = {
    "faq-v1": "너는 쇼핑몰 고객센터 상담원이다. [근거]에 있는 내용만 사용해 2문장 이내로 답하고, "
              "끝에 근거 id를 [D1]처럼 붙여라. 근거가 없으면 '상담원 연결이 필요합니다'라고 답하라.",
}
PRICE_PER_1M = {"input": 0.0, "output": 0.0}   # 사용하는 모델의 단가(USD/100만 토큰)로 채운다

def mock_answer(hits, idx):
    if not hits:
        return "상담원 연결이 필요합니다."
    d = idx["docs"][hits[0]["i"]]
    return f"{d['text']} [{d['id']}]"

def generate(q, hits, idx, cfg):
    if not cfg.get("use_llm") or not os.getenv("OPENAI_API_KEY"):
        return mock_answer(hits, idx), {"input": 0, "output": 0}, "mock"
    ctx = "\n".join(f"[{idx['docs'][h['i']]['id']}] {idx['docs'][h['i']]['title']}: {idx['docs'][h['i']]['text']}"
                    for h in hits) or "(근거 없음)"
    try:
        from openai import OpenAI
        resp = OpenAI().chat.completions.create(
            model=cfg["llm_model"], temperature=cfg["temperature"],
            messages=[{"role": "system", "content": PROMPTS[cfg["prompt_version"]]},
                      {"role": "user", "content": f"[근거]\n{ctx}\n\n[질문]\n{clean_text(q, idx['synonyms'])}"}])
        u = resp.usage
        return resp.choices[0].message.content, {"input": u.prompt_tokens, "output": u.completion_tokens}, "openai"
    except Exception as e:                    # API 장애가 나도 서비스는 멈추지 않게
        return mock_answer(hits, idx), {"input": 0, "output": 0}, f"fallback:{type(e).__name__}"


# %% [8] 데이터 불러오기와 검증 — 나쁜 데이터는 여기서 멈춘다
def load_data():
    docs = [{"id": r["id"].strip(), "title": r["title"].strip(), "text": r["text"].strip()} for r in read_csv(FAQ_FILE)]
    return docs, load_synonyms(), read_jsonl(EVAL_FILE)

def validate(docs, synonyms, evals):
    errors, ids = [], [d["id"] for d in docs]
    for d in docs:
        if not (d["id"] and d["title"] and d["text"]):
            errors.append(f"FAQ {d['id'] or '(id 없음)'}: 빈 항목이 있음")
        if mask_pii(d["title"] + d["text"]) != d["title"] + d["text"]:
            errors.append(f"FAQ {d['id']}: 개인정보(전화번호·주민번호·이메일)가 들어 있음")
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"FAQ id 중복: {dup}")
    for p, _, _ in synonyms:
        try:
            re.compile(p)
        except re.error:
            errors.append(f"동의어 사전: 잘못된 정규식 '{p}'")
    for e in evals:
        if e["gold"] not in ids:
            errors.append(f"평가셋: '{e['q']}'의 정답 {e['gold']}가 FAQ에 없음")
    for check in CUSTOM_CHECKS:
        errors += check(docs, evals)
    return errors


# %% [9] 회귀 평가 — 평가셋 전체를 다시 채점하고, 활성 버전과 비교한다
def evaluate(idx, evals, cfg):
    rows = []
    for e in evals:
        hits = search(e["q"], idx, cfg)
        ids = [h["id"] for h in hits]
        ans, _, _ = generate(e["q"], hits, idx, cfg)
        rows.append({"q": e["q"], "gold": e["gold"], "top": ids,
                     "hit1": bool(ids) and ids[0] == e["gold"], "hit3": e["gold"] in ids,
                     "cited": f"[{e['gold']}]" in ans, "must_pass": e.get("must_pass", False)})
    n = max(len(rows), 1)
    metrics = {k: round(sum(r[f] for r in rows) / n, 2) for k, f in
               [("hit1", "hit1"), ("hit3", "hit3"), ("cite_rate", "cited")]}
    return metrics, rows

def new_failures(rows, prev_rows):
    """활성 버전에서는 맞혔는데 이번에 틀린 질문 = 회귀(regression)"""
    before = {r["q"]: r["hit1"] for r in prev_rows}
    return [r["q"] for r in rows if before.get(r["q"]) and not r["hit1"]]


# %% [10] 버전 레지스트리 — 어떤 버전이 활성인지, 이력은 어떤지
def load_registry():
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {"active": None, "history": [], "versions": {}, "last_seen": {}}

def save_registry(reg):
    REGISTRY_FILE.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

def manifest_of(version):
    return json.loads((ART / version / "manifest.json").read_text(encoding="utf-8"))

def rollback():
    reg = load_registry()
    if not reg["history"]:
        print("되돌릴 이전 버전이 없습니다.")
        return
    old = reg["active"]
    reg["active"] = reg["history"].pop()
    reg["versions"][old]["status"] = "롤백됨"
    reg["versions"][reg["active"]]["status"] = "활성"
    save_registry(reg)
    print(f"↩️ 롤백: {old} → {reg['active']}")


# %% [11] 파이프라인 — 검증 → 정제·색인 → 회귀 평가 → 게이트 → 활성 버전 교체
def run_pipeline(reason="수동 실행", fp=None):
    reg = load_registry()
    version = f"v{len(reg['versions']) + 1:03d}"
    print(f"▶ 파이프라인 {version} 시작 — {reason}")
    rec = {"version": version, "time": now(), "reason": reason, "config": CONFIG}

    docs, synonyms, evals = load_data()                                   # ① 검증
    errors = validate(docs, synonyms, evals)
    if errors:
        print("  ① 데이터 검증 ⛔ 중단")
        for e in errors:
            print("     -", e)
        rec.update(status="검증 실패", errors=errors)
        reg["versions"][version] = {"status": "검증 실패", "time": rec["time"], "reason": reason}
        save_registry(reg)
        append_jsonl(LOGS / "pipeline_runs.jsonl", rec)
        print(f"  → 활성 버전 그대로: {reg['active']}")
        return rec
    print(f"  ① 데이터 검증 ✅ FAQ {len(docs)}건 · 사전 {len(synonyms)}건 · 평가 {len(evals)}건")

    idx = make_index(docs, synonyms, CONFIG)                              # ② 정제·색인
    print(f"  ② 정제·색인 ✅ TF-IDF {idx['X'].shape} · BERT {'있음' if idx['emb'] is not None else '없음'}")

    metrics, rows = evaluate(idx, evals, CONFIG)                          # ③ 회귀 평가
    prev = reg["active"]
    fails = new_failures(rows, manifest_of(prev)["rows"]) if prev else []
    print(f"  ③ 회귀 평가 Hit@1 {metrics['hit1']:.2f} · Hit@3 {metrics['hit3']:.2f} · "
          f"인용률 {metrics['cite_rate']:.2f} · 새로 틀린 질문 {len(fails)}")
    for r in rows:
        if not r["hit1"]:
            print(f"     ✗ {r['q']}  정답 {r['gold']}  검색 {r['top']}")

    result = {"metrics": metrics, "rows": rows, "new_fails": fails}       # ④ 게이트
    checks = [(metrics["hit1"] >= GATE["hit1"], f"Hit@1 ≥ {GATE['hit1']}"),
              (metrics["cite_rate"] >= GATE["cite_rate"], f"인용률 ≥ {GATE['cite_rate']}"),
              (len(fails) <= GATE["max_new_fail"], f"새로 틀린 질문 ≤ {GATE['max_new_fail']}")]
    checks += [g(result) for g in CUSTOM_GATES]
    passed = all(ok for ok, _ in checks)
    for ok, msg in checks:
        if not ok:
            print(f"     ⛔ 기준 미달: {msg}")
    for q in fails:
        print(f"     ⛔ 회귀: '{q}' — {prev}에서는 맞혔음")

    status = "활성" if passed else "보류"
    save_index(version, idx, {"version": version, "time": rec["time"], "reason": reason, "config": CONFIG,
                              "metrics": metrics, "rows": rows, "new_fails": fails, "status": status})
    reg["versions"][version] = {"status": status, "time": rec["time"], "reason": reason, "metrics": metrics, "fp": fp}
    if passed:                                                            # ⑤ 활성 버전 교체
        if prev:
            reg["history"].append(prev)
            reg["versions"][prev]["status"] = "이전"
        reg["active"] = version
        print(f"  ④ 게이트 ✅ 통과 → {version} 활성 (이전 {prev})")
    else:
        print(f"  ④ 게이트 ⛔ 보류 → 활성 버전 그대로: {prev}")
    save_registry(reg)
    rec.update(status=status, metrics=metrics, new_fails=fails)
    append_jsonl(LOGS / "pipeline_runs.jsonl", rec)
    return rec


# %% [12] 변경 감지 — 데이터 파일이나 설정이 바뀌었으면 파이프라인 실행
def fingerprint():
    fp = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:12] for p in (FAQ_FILE, SYN_FILE, EVAL_FILE)}
    fp["CONFIG"] = hashlib.sha256(json.dumps(CONFIG, sort_keys=True).encode()).hexdigest()[:12]
    return fp

def check_and_run(force=False, quiet=False):
    reg = load_registry()
    fp = fingerprint()
    changed = [k for k in fp if reg["last_seen"].get(k) != fp[k]]
    if not changed and not force:
        if not quiet:
            print(f"변경 없음 — 활성 버전 {reg['active']}")
        return None
    reg["last_seen"] = fp
    save_registry(reg)
    active = reg["versions"].get(reg["active"] or "", {})
    if active.get("fp") == fp and not force:
        print(f"변경 감지: {', '.join(changed)} — 활성 버전 {reg['active']}와 같은 데이터로 돌아와 실행 생략")
        return None
    return run_pipeline("변경 감지: " + ", ".join(changed) if changed else "강제 실행", fp)


# %% [13] 서빙 — 활성 버전으로 답하고 모든 요청을 로그로 남긴다
_serving = {}

def ask(q, show=True):
    reg = load_registry()
    version = reg["active"]
    if version is None:
        print("아직 활성 버전이 없습니다. check_and_run()을 먼저 실행하세요.")
        return None
    if _serving.get("version") != version:                # 활성 버전이 바뀌면 새 색인을 불러온다
        _serving.update(version=version, idx=load_index(version, CONFIG))
    idx = _serving["idx"]
    t0 = time.time()
    hits = search(q, idx, CONFIG)
    ans, usage, mode = generate(q, hits, idx, CONFIG)
    rec = {"trace_id": uuid.uuid4().hex[:8], "time": now(), "version": version, "mode": mode,
           "query": mask_pii(q),                           # 로그에는 개인정보를 지운 질문만
           "retrieved": [h["id"] for h in hits], "top_score": hits[0]["score"] if hits else 0.0,
           "no_hit": not hits, "latency_ms": round((time.time() - t0) * 1000, 1), "tokens": usage,
           "cost_usd": round(usage["input"] / 1e6 * PRICE_PER_1M["input"]
                             + usage["output"] / 1e6 * PRICE_PER_1M["output"], 6),
           "answer": ans}
    append_jsonl(LOGS / "serve_log.jsonl", rec)
    if show:
        print(f"[{rec['trace_id']} · {version}] {rec['query']}\n   → {ans}")
    return rec


# %% [14] 피드백 · 검토 큐 · 모니터링
def feedback(trace_id, good, comment=""):
    log = {r["trace_id"]: r for r in read_jsonl(LOGS / "serve_log.jsonl")}[trace_id]
    append_jsonl(LOGS / "feedback.jsonl", {"trace_id": trace_id, "time": now(), "version": log["version"],
                                           "good": good, "comment": comment})
    if not good:                                           # 👎는 사람이 검토할 큐로
        append_jsonl(LOGS / "review_queue.jsonl", {"trace_id": trace_id, "time": now(), "query": log["query"],
                                                   "retrieved": log["retrieved"], "version": log["version"],
                                                   "status": "대기"})

def review_queue():
    items = [r for r in read_jsonl(LOGS / "review_queue.jsonl") if r["status"] == "대기"]
    for r in items:
        print(f"  {r['trace_id']}  {r['query']}  (검색 {r['retrieved'] or '없음'}, {r['version']})")
    return items

def monitor(version=None):
    logs = [r for r in read_jsonl(LOGS / "serve_log.jsonl") if version in (None, r["version"])]
    fbs = [r for r in read_jsonl(LOGS / "feedback.jsonl") if version in (None, r["version"])]
    if not logs:
        print("로그가 없습니다.")
        return {}
    m = {"requests": len(logs),
         "no_hit_rate": round(sum(r["no_hit"] for r in logs) / len(logs), 2),
         "bad_feedback_rate": round(sum(not f["good"] for f in fbs) / len(fbs), 2) if fbs else 0.0,
         "p95_latency_ms": round(float(np.percentile([r["latency_ms"] for r in logs], 95)), 1),
         "cost_usd": round(sum(r["cost_usd"] for r in logs), 4)}
    for name, fn in CUSTOM_METRICS.items():
        m[name] = fn(logs, fbs)
    print(f"모니터링 ({version or '전체 버전'})")
    for k, v in m.items():
        alarm = k in ALERT and v > ALERT[k]
        print(f"  {k:<18} {v:<8} {'🚨 경보 (기준 ' + str(ALERT[k]) + ')' if alarm else ''}")
    return m


# %% [15] 운영자 도구 — 사람이 하는 일은 '데이터 파일 수정'뿐이다
def add_faq(id, title, text):
    rows = read_csv(FAQ_FILE) + [{"id": id, "title": title, "text": text}]
    write_csv(FAQ_FILE, ["id", "title", "text"], [[r["id"], r["title"], r["text"]] for r in rows])
    print(f"faq.csv에 {id} 추가")

def edit_faq(id, title=None, text=None):
    rows = read_csv(FAQ_FILE)
    for r in rows:
        if r["id"] == id:
            r["title"] = title or r["title"]
            r["text"] = text or r["text"]
    write_csv(FAQ_FILE, ["id", "title", "text"], [[r["id"], r["title"], r["text"]] for r in rows])
    print(f"faq.csv의 {id} 수정")

def remove_faq(id):
    rows = [r for r in read_csv(FAQ_FILE) if r["id"] != id]
    write_csv(FAQ_FILE, ["id", "title", "text"], [[r["id"], r["title"], r["text"]] for r in rows])
    print(f"faq.csv에서 {id} 삭제")

def add_synonym(pattern, replace, note=""):
    rows = read_csv(SYN_FILE) + [{"pattern": pattern, "replace": replace, "note": note}]
    write_csv(SYN_FILE, ["pattern", "replace", "note"], [[r["pattern"], r["replace"], r["note"]] for r in rows])
    print(f"synonyms.csv에 '{pattern}' → '{replace}' 추가")

def add_eval(q, gold, source="수동", must_pass=False):
    rec = {"q": q, "gold": gold, "source": source}
    if must_pass:
        rec["must_pass"] = True
    append_jsonl(EVAL_FILE, rec)
    print(f"eval_set.jsonl에 추가: '{q}' → {gold}")

def label(trace_id, gold):
    """검토 큐의 질문에 정답 FAQ를 달아 평가셋으로 보낸다."""
    path = LOGS / "review_queue.jsonl"
    items = read_jsonl(path)
    for r in items:
        if r["trace_id"] == trace_id and r["status"] == "대기":
            r["status"] = f"라벨링 완료 → {gold}"
            add_eval(r["query"], gold, source=f"피드백 {trace_id}")
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items), encoding="utf-8")

def status():
    reg = load_registry()
    print(f"활성 버전: {reg['active']}   이력: {reg['history']}")
    for v, info in reg["versions"].items():
        m = info.get("metrics", {})
        score = f"Hit@1 {m['hit1']:.2f}" if m else ""
        print(f"  {v}  {info['status']:<6} {score:<11} {info['reason']}")
