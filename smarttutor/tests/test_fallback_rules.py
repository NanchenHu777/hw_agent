import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.guardrail_agent import guardrail_agent
from agents.triage_agent import triage_agent
from agents.conversation import conversation_manager


def test_triage_fallback_handles_short_core_cases():
    assert triage_agent._fallback_classification("x+1=2")["category"] == "valid_math"
    assert triage_agent._fallback_classification("谁是法国第一任总统？")["category"] == "valid_history"
    assert triage_agent._fallback_classification("我是大一学生")["action"] == "handle_grade_info"
    assert triage_agent._fallback_classification("我是小学生")["action"] == "handle_grade_info"
    assert triage_agent._fallback_classification("Can you explain calculus?")["category"] == "valid_math"
    assert triage_agent._fallback_classification("总结我们的对话")["action"] == "handle_summarize"


def test_conversation_extract_grade_handles_primary_school():
    assert conversation_manager.extract_grade_from_message("我是小学生") == "小学生"
    assert conversation_manager.extract_grade_from_message("I am a primary school student") == "小学生"


def test_triage_prefers_obvious_math_fallback_when_llm_is_too_strict(monkeypatch):
    monkeypatch.setattr(
        triage_agent.llm_client,
        "structured_output",
        lambda **kwargs: {
            "category": "invalid",
            "intent": "chit_chat",
            "reason": "too broad",
            "action": "respond_rejection",
        },
    )

    result = triage_agent.classify_sync("Can you explain calculus?")

    assert result["category"] == "valid_math"
    assert result["action"] == "handoff_to_math"


def test_guardrail_rule_based_check_rejects_travel_question():
    should_reject, message = guardrail_agent._rule_based_check("去伦敦怎么走？")

    assert should_reject is True
    assert "不是一个数学或历史作业问题" in message


def test_guardrail_rule_based_check_rejects_too_local_question():
    should_reject, message = guardrail_agent._rule_based_check("HKUST第一任校长是谁？")

    assert should_reject is True
    assert "本地化" in message or "小众" in message
