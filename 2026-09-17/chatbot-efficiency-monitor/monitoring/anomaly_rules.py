from __future__ import annotations

import pandas as pd


def detect_hourly_anomalies(df: pd.DataFrame) -> list[dict]:
    """최근 집계 구간의 운영 이상징후 후보를 찾는다.

    특정 직원의 사용량이 많다는 이유만으로 문제로 판단하지 않는다.
    오류/재시도/세션당 토큰/해결률/반복 잡담 등을 함께 본다.
    """
    if df.empty:
        return []

    alerts: list[dict] = []
    work = df.copy()
    work["total_tokens"] = work["input_tokens"].fillna(0) + work["output_tokens"].fillna(0)

    api_rows = work[(work["api_call_count"].fillna(0) > 0) | (work["api_required"].fillna(0) > 0)]

    # 1) API 최종 오류: 호출 수가 적더라도 최종 실패는 확인 가치가 높다.
    errors = work[~work["status_code"].fillna(0).astype(int).isin([0, 200])]
    if not errors.empty:
        counts = errors["error_type"].fillna("unknown").value_counts().to_dict()
        severity = "high" if len(errors) >= 3 else "medium"
        alerts.append(
            {
                "severity": severity,
                "alert_type": "api_error",
                "employee_id": None,
                "message": f"최근 집계 구간 API 최종 오류 {len(errors)}건 발생: {counts}",
            }
        )

    # 2) API 오류율 증가.
    actual_api = work[work["api_call_count"].fillna(0) > 0]
    if len(actual_api) >= 10:
        error_rate = len(errors) / len(actual_api)
        if error_rate >= 0.10:
            alerts.append(
                {
                    "severity": "high",
                    "alert_type": "api_error_rate",
                    "employee_id": None,
                    "message": f"최근 API 오류율이 {error_rate * 100:.1f}%입니다. 429/Timeout/5xx와 외부 API 상태를 확인하세요.",
                }
            )

    # 3) 재시도 증가: 비용 증가나 Rate Limit/Timeout 문제일 수 있다.
    retry_total = int(work["retry_count"].fillna(0).sum())
    if retry_total >= 5:
        alerts.append(
            {
                "severity": "medium",
                "alert_type": "retry_spike",
                "employee_id": None,
                "message": f"최근 집계 구간 API 재시도 {retry_total}회 발생. Timeout/429/5xx와 최대 재시도 횟수를 확인하세요.",
            }
        )

    # 4) 세션당 토큰 과다: 긴 Context/RAG 문서 과다/출력 길이를 우선 확인한다.
    heavy_sessions = work[work["total_tokens"] >= 6000]
    if not heavy_sessions.empty:
        alerts.append(
            {
                "severity": "medium",
                "alert_type": "high_token_session",
                "employee_id": None,
                "message": f"세션당 6,000 token 이상 사용 {len(heavy_sessions)}건. Context, RAG Top-K, 답변 길이 제한을 확인하세요.",
            }
        )

    # 5) 직원별 토큰 이상치. 부서 평균 대비 차이가 큰 경우만 '확인 후보'로 기록한다.
    token_rows = work[work["total_tokens"] > 0]
    if not token_rows.empty:
        per_emp = token_rows.groupby(["department", "employee_id"], as_index=False).agg(
            sessions=("session_id", "count"),
            total_tokens=("total_tokens", "sum"),
            retries=("retry_count", "sum"),
        )
        dept_avg = per_emp.groupby("department")["total_tokens"].mean().rename("dept_avg")
        per_emp = per_emp.join(dept_avg, on="department")
        suspicious = per_emp[
            (per_emp["sessions"] >= 3)
            & (per_emp["total_tokens"] >= 15000)
            & (per_emp["total_tokens"] >= per_emp["dept_avg"] * 3)
        ]
        for _, row in suspicious.iterrows():
            alerts.append(
                {
                    "severity": "medium",
                    "alert_type": "employee_token_outlier",
                    "employee_id": row["employee_id"],
                    "message": (
                        f"직원 {row['employee_id']}의 token 사용량 {int(row['total_tokens']):,}이 "
                        f"같은 문의 부서 평균 {row['dept_avg']:.0f}의 3배 이상입니다. "
                        "개인 사용 문제로 단정하지 말고 질문 수, 세션당 input token, RAG context, retry 여부를 함께 확인하세요."
                    ),
                }
            )

    # 6) 해결률 급락 후보. 표본이 너무 작은 구간은 알림하지 않는다.
    business = work[~work["route"].isin(["NON_WORK", "SECURITY_ESCALATE"])]
    if len(business) >= 10:
        rate = float(business["resolved"].fillna(0).mean())
        if rate < 0.50:
            alerts.append(
                {
                    "severity": "medium",
                    "alert_type": "low_resolution_rate",
                    "employee_id": None,
                    "message": f"최근 업무질문 해결률이 {rate * 100:.1f}%입니다. FAQ/RAG 문서 품질과 상담원 전환 증가 여부를 확인하세요.",
                }
            )

    # 7) 명백한 잡담이 반복될 때만 낮은 우선순위로 기록한다.
    non_work = work[work["route"] == "NON_WORK"]
    if not non_work.empty:
        counts = non_work.groupby("employee_id").size()
        for emp, count in counts[counts >= 5].items():
            alerts.append(
                {
                    "severity": "low",
                    "alert_type": "repeated_non_work",
                    "employee_id": emp,
                    "message": f"직원 {emp}에서 최근 구간 명백한 잡담 요청이 {int(count)}회 기록되었습니다.",
                }
            )

    return alerts
