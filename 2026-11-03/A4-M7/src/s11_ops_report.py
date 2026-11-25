# ====================================================================
# Step 11 · 운영 리포트 — 성능·비용·안정성·기준선 비교·Alert
#   입력: outputs/answer_log.jsonl (s09), outputs/answer_eval.csv (s10)
#   출력: outputs/ops_metrics.json, latency_by_stage.csv, alerts.csv, query_type_mix.csv
# 실행:  python src/s11_ops_report.py                  (지금 값 계산 + 기준선과 비교)
#        python src/s11_ops_report.py --save-baseline  (지금 값을 기준선으로 저장)
# ====================================================================
import csv
import json
import sys
from collections import Counter

from config import OUT_DIR
from config_ops import ALERT_ABS, ALERT_REL, USD_KRW

BASELINE = OUT_DIR / "baseline.json"


def pct(xs, p):
    """백분위수 (nearest-rank). P95 = 95%의 요청이 이 값 안에 끝남."""
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = max(1, -(-len(xs) * p // 100))   # ceil
    return float(xs[int(k) - 1])


def load():
    logs = [json.loads(l) for l in open(OUT_DIR / "answer_log.jsonl", encoding="utf-8")]
    ev = {r["query_id"]: r for r in csv.DictReader(open(OUT_DIR / "answer_eval.csv", encoding="utf-8-sig"))}
    return logs, ev


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


def metrics(logs, ev):
    ok = [r for r in logs if not r["error"]]
    m = {"backend": logs[0]["backend"], "model": logs[0]["model"], "k": logs[0]["k"],
         "prompt_version": logs[0]["prompt_version"], "requests": len(logs)}
    # --- 품질 (s10 결과)
    ans = [ev[r["query_id"]] for r in ok if r["answerable"]]
    na = [ev[r["query_id"]] for r in ok if not r["answerable"]]
    m["retrieval_hit"] = mean([1.0 if e["retrieval_hit"] == "True" else 0.0 for e in ans])
    m["grounded_rule"] = mean([fnum(e["grounded_rule"]) for e in ans])
    m["citation_valid"] = mean([fnum(e["citation_valid"]) for e in ans])
    m["keyword_cov"] = mean([fnum(e["keyword_cov"]) for e in ans])
    m["abstention_accuracy"] = mean([1.0 if e["abstained"] == "True" else 0.0 for e in na])
    m["pass_rate"] = mean([1.0 if ev[r["query_id"]]["verdict"] == "PASS" else 0.0 for r in logs])
    # --- 성능
    for stage in ["retrieval_ms", "llm_ms", "e2e_ms"]:
        xs = [r[stage] for r in ok]
        m[f"{stage[:-3]}_avg_ms"] = round(sum(xs) / len(xs), 1)
        for p in (50, 95, 99):
            m[f"{stage[:-3]}_p{p}_ms"] = round(pct(xs, p), 1)
    # --- 토큰·비용
    m["avg_context_chars"] = round(mean([r["context_chars"] for r in ok]), 1)
    m["avg_input_tokens"] = round(mean([r["input_tokens"] for r in ok]), 1)
    m["avg_output_tokens"] = round(mean([r["output_tokens"] for r in ok]), 1)
    m["total_cost_usd"] = round(sum(r["cost_usd"] for r in ok), 6)
    m["cost_per_q_usd"] = round(m["total_cost_usd"] / len(ok), 8)
    m["cost_per_1000q_krw"] = round(m["cost_per_q_usd"] * 1000 * USD_KRW, 1)
    # --- 안정성
    m["error_rate"] = round(sum(bool(r["error"]) for r in logs) / len(logs), 4)
    m["retry_rate"] = round(sum(r["retries"] > 0 for r in logs) / len(logs), 4)
    retried = [r for r in logs if r["retries"] > 0]
    m["recovery_rate"] = round(sum(not r["error"] for r in retried) / len(retried), 4) if retried else None
    return m


def check_alerts(m, base):
    alerts = []
    for k, (op, th) in ALERT_ABS.items():
        v = m.get(k)
        if v is None:
            continue
        bad = v < th if op == ">=" else v > th
        if bad:
            alerts.append({"type": "절대기준", "metric": k, "value": v, "rule": f"{op} {th}", "baseline": ""})
    if base:
        for k, (direction, ratio) in ALERT_REL.items():
            v, b = m.get(k), base.get(k)
            if v is None or not b:
                continue
            change = (v - b) / b
            if (direction == "up" and change > ratio) or (direction == "down" and change < -ratio):
                alerts.append({"type": "기준선대비", "metric": k, "value": v,
                               "rule": f"{'+' if direction == 'up' else '-'}{int(ratio * 100)}% 넘게 변화 ({change:+.0%})",
                               "baseline": b})
    return alerts


if __name__ == "__main__":
    logs, ev = load()
    m = metrics(logs, ev)
    if "--save-baseline" in sys.argv:
        BASELINE.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        print("기준선 저장 → outputs/baseline.json")
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else None
    (OUT_DIR / "ops_metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(OUT_DIR / "latency_by_stage.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["query_id", "retrieval_ms", "prompt_ms", "llm_ms", "e2e_ms", "input_tokens", "output_tokens", "error"])
        for r in logs:
            w.writerow([r["query_id"], r["retrieval_ms"], r["prompt_ms"], r["llm_ms"], r["e2e_ms"], r["input_tokens"], r["output_tokens"], r["error"] or ""])
    mix = Counter(r["query_type"] for r in logs)
    with open(OUT_DIR / "query_type_mix.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["query_type", "count", "ratio"])
        for t, c in mix.most_common():
            w.writerow([t, c, round(c / len(logs), 3)])
    alerts = check_alerts(m, base)
    with open(OUT_DIR / "alerts.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["type", "metric", "value", "rule", "baseline"]); w.writeheader(); w.writerows(alerts)

    print(f"[{m['backend']}] model={m['model']} K={m['k']} 요청 {m['requests']}건")
    print(f"품질   검색Hit {m['retrieval_hit']}  근거성 {m['grounded_rule']}  인용유효 {m['citation_valid']}  "
          f"키워드 {m['keyword_cov']}  보류정확 {m['abstention_accuracy']}  PASS {m['pass_rate']}")
    print(f"시간   검색 avg {m['retrieval_avg_ms']}ms | LLM avg {m['llm_avg_ms']} p95 {m['llm_p95_ms']} | "
          f"E2E avg {m['e2e_avg_ms']} p50 {m['e2e_p50_ms']} p95 {m['e2e_p95_ms']} p99 {m['e2e_p99_ms']}")
    print(f"비용   context {m['avg_context_chars']}자  in {m['avg_input_tokens']} out {m['avg_output_tokens']} tok  "
          f"질문당 ${m['cost_per_q_usd']:.6f}  1,000건당 약 {m['cost_per_1000q_krw']}원")
    print(f"안정성 오류율 {m['error_rate']}  재시도율 {m['retry_rate']}  복구율 {m['recovery_rate']}")
    if base:
        print("\n기준선 대비:")
        for k in ["retrieval_hit", "grounded_rule", "avg_input_tokens", "cost_per_q_usd", "e2e_p95_ms", "error_rate"]:
            if base.get(k) is not None and m.get(k) is not None:
                print(f"  {k:18} {base[k]} → {m[k]}")
    print(f"\nAlert {len(alerts)}건" + ("" if not alerts else ":"))
    for a in alerts:
        print(f"  [{a['type']}] {a['metric']} = {a['value']}  (규칙 {a['rule']})")
