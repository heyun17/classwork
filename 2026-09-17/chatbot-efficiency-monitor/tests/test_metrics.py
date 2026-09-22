from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.metrics import baseline_metrics, chatbot_metrics
from chatbot.router import route_question


def faq_df():
    return pd.read_csv(ROOT / "data" / "faq.csv")


def test_baseline_average_monthly_inquiries():
    df = pd.read_csv(ROOT / "data" / "pre_chatbot_inquiries.csv")
    result = baseline_metrics(df)
    assert round(result["avg_monthly_inquiries"]) == 500


def test_chatbot_metrics_have_sessions():
    df = pd.read_csv(ROOT / "data" / "chatbot_logs.csv")
    result = chatbot_metrics(df)
    assert result["sessions"] == len(df)
    assert 0 <= result["no_api_rate"] <= 100


def test_payroll_question_is_business_faq():
    result = route_question("월급이 아직 안들어왔어", faq_df())
    assert result["route"] == "TEXT_FAQ"
    assert result["use_api"] is False


def test_cafeteria_question_is_not_blocked():
    result = route_question("구내식당 메뉴 알려줘", faq_df())
    assert result["route"] == "LLM_REQUIRED"
    assert result["use_api"] is True


def test_internet_problem_is_not_blocked():
    result = route_question("인터넷 연결이 안돼", faq_df())
    assert result["route"] == "LLM_REQUIRED"
    assert result["use_api"] is True


def test_ambiguous_hr_question_is_not_blocked():
    result = route_question("출산휴가 신청은 어디서 해?", faq_df())
    assert result["route"] == "LLM_REQUIRED"
    assert result["use_api"] is True


def test_obvious_chat_questions_are_blocked():
    for question in ["심심해", "나랑 놀자", "지금 뭐해?", "끝말잇기 하자"]:
        result = route_question(question, faq_df())
        assert result["route"] == "NON_WORK"
        assert result["use_api"] is False


def test_non_work_ratio_is_conservative():
    df = pd.read_csv(ROOT / "data" / "chatbot_logs.csv")
    ratio = df["route"].eq("NON_WORK").mean()
    assert ratio <= 0.02
