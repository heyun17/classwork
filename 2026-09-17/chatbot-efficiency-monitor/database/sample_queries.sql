-- 1. 챗봇 월별 사용량
SELECT substr(created_at, 1, 7) AS month, COUNT(*) AS sessions
FROM chatbot_logs
GROUP BY substr(created_at, 1, 7)
ORDER BY month;

-- 2. API를 사용하지 않은 비율
SELECT ROUND(AVG(CASE WHEN input_tokens = 0 THEN 1.0 ELSE 0.0 END) * 100, 2) AS no_api_rate_pct
FROM chatbot_logs;

-- 3. 업무 질문 해결률
SELECT ROUND(AVG(resolved) * 100, 2) AS resolution_rate_pct
FROM chatbot_logs
WHERE route <> 'NON_WORK';

-- 4. 부서별 상담원 전환율
SELECT department,
       ROUND(AVG(escalated) * 100, 2) AS escalation_rate_pct
FROM chatbot_logs
WHERE route <> 'NON_WORK'
GROUP BY department
ORDER BY escalation_rate_pct DESC;

-- 5. 토큰 사용량이 큰 카테고리
SELECT category,
       SUM(input_tokens + output_tokens) AS total_tokens,
       ROUND(SUM(api_cost_krw), 2) AS api_cost_krw
FROM chatbot_logs
GROUP BY category
ORDER BY total_tokens DESC
LIMIT 10;

-- 6. 비효율 후보
SELECT session_id, created_at, department, category,
       resolution_seconds, message_count, input_tokens, output_tokens
FROM chatbot_logs
WHERE anomaly_flag = 1
   OR resolution_seconds > 240
   OR message_count >= 9
   OR input_tokens >= 2200
ORDER BY created_at DESC;
