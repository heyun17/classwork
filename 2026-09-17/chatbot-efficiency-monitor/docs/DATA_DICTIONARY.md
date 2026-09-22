# 데이터 정의서

## pre_chatbot_inquiries
| 컬럼 | 설명 |
|---|---|
| inquiry_id | 도입 전 문의 식별자 |
| created_at | 문의 시각 |
| department | 담당 부서 |
| category | 문의 유형 |
| human_handle_minutes | 사람이 처리한 시간(분) |
| resolved | 해결 여부 |

## chatbot_logs
| 컬럼 | 설명 |
|---|---|
| session_id | 챗봇 문의 세션 식별자 |
| created_at | 문의 발생 시각 |
| employee_id | 익명화된 직원 ID |
| department | 관련 지원 부서 |
| category | 문의 유형 |
| question_text | 테스트용 질문 문장 |
| question_type | menu / text |
| route | MENU_FAQ / TEXT_FAQ / SECURITY_ESCALATE / NON_WORK / LLM |
| resolved | 챗봇 단계에서 해결 여부 |
| escalated | 담당자 전환 여부 |
| resolution_seconds | 챗봇 단계 처리시간 |
| message_count | 한 세션의 대화 횟수 |
| input_tokens/output_tokens | LLM 사용 토큰 |
| api_call_count | 실제 API 호출 횟수(재시도 포함) |
| retry_count | API 재시도 횟수 |
| status_code | 최종 API 상태 코드. API 미사용은 0 |
| error_type | rate_limit / timeout / server_error 등 |
| api_cost_krw | 실습용 가정 단가 기반 변동비 |
| human_handle_minutes | 담당자 전환 후 사람이 처리한 시간 |
| anomaly_flag | 잡담, 오류, 과도한 토큰 등 점검 후보 |

### NON_WORK 분류 원칙
업무 외 질문 차단은 보수적으로 적용한다. `심심해`, `놀자`, `뭐해`, `끝말잇기 하자`처럼 명백한 잡담/놀이 요청만 NON_WORK로 기록한다.

`월급`, `구내식당`, `인터넷`, `복지`, `규정`처럼 회사 업무와 연결될 가능성이 있는 질문은 FAQ에 없더라도 바로 차단하지 않고 LLM 처리 대상으로 보낸다.

## faq
반복 질문 메뉴와 키워드 답변. 이 테이블에서 해결되는 질문은 LLM API를 호출하지 않는다.

## system_metrics
CPU, 메모리, API 지연, 오류 수. 성과 KPI가 아니라 장애 원인 확인용 보조 데이터다.

## company_profile
직원 수, 회사 특성, 인건비와 비용 가정값을 저장한다.
