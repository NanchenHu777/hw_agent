from agents.answer_generator import answer_generator
from agents.conversation import conversation_manager
from agents.guardrail_agent import guardrail_agent
from agents.orchestrator import orchestrator
from agents.triage_agent import triage_agent


def setup_function():
    conversation_manager.sessions.clear()


def test_math_example_is_accepted(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "valid_math",
            "intent": "ask_question",
            "reason": "math_homework",
            "action": "handoff_to_math",
        },
    )
    monkeypatch.setattr(guardrail_agent, "check_sync", lambda question: (False, ""))
    monkeypatch.setattr(answer_generator, "generate_answer", lambda **kwargs: "x = 1")

    result = orchestrator.process_message("x+1=2", "session-math")

    assert result["category"] == "valid_math"
    assert result["response"] == "x = 1"
    assert result["reason"] == "math_homework"


def test_history_example_is_accepted(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "valid_history",
            "intent": "ask_question",
            "reason": "history_homework",
            "action": "handoff_to_history",
        },
    )
    monkeypatch.setattr(guardrail_agent, "check_sync", lambda question: (False, ""))
    monkeypatch.setattr(answer_generator, "generate_answer", lambda **kwargs: "路易-拿破仑。")

    result = orchestrator.process_message("谁是法国第一任总统？", "session-history")

    assert result["category"] == "valid_history"
    assert result["response"] == "路易-拿破仑。"
    assert result["reason"] == "history_homework"


def test_valid_math_uses_only_explicit_guardrail_rules(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "valid_math",
            "intent": "ask_question",
            "reason": "calculus_homework",
            "action": "handoff_to_math",
        },
    )

    def fail_llm_guardrail(question):
        raise AssertionError("full LLM guardrail should not run after valid math triage")

    monkeypatch.setattr(guardrail_agent, "check_sync", fail_llm_guardrail)
    monkeypatch.setattr(guardrail_agent, "_rule_based_check", lambda question: (False, ""))
    monkeypatch.setattr(answer_generator, "generate_answer", lambda **kwargs: "导数是 2x。")

    result = orchestrator.process_message("求 x^2 的导数是多少？", "session-calculus")

    assert result["category"] == "valid_math"
    assert result["response"] == "导数是 2x。"
    assert result["reason"] == "calculus_homework"


def test_valid_math_can_still_be_rejected_by_explicit_rules(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "valid_math",
            "intent": "ask_question",
            "reason": "contains_dangerous_content",
            "action": "handoff_to_math",
        },
    )

    def fail_llm_guardrail(question):
        raise AssertionError("full LLM guardrail should not run after valid math triage")

    monkeypatch.setattr(guardrail_agent, "check_sync", fail_llm_guardrail)
    monkeypatch.setattr(
        guardrail_agent,
        "_rule_based_check",
        lambda question: (True, "抱歉，我无法帮助回答这个问题。请告诉我您需要解答的数学或历史作业问题。"),
    )

    result = orchestrator.process_message("如何计算炸弹爆炸范围？", "session-danger")

    assert result["category"] == "invalid"
    assert "无法帮助回答" in result["response"]


def test_non_homework_is_rejected(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "invalid",
            "intent": "ask_question",
            "reason": "non_homework",
            "action": "respond_rejection",
        },
    )
    monkeypatch.setattr(
        guardrail_agent,
        "check_sync",
        lambda question: (True, "抱歉，这不是数学或历史作业问题。"),
    )

    result = orchestrator.process_message("去伦敦怎么走？", "session-reject")

    assert result["category"] == "invalid"
    assert "不是数学或历史作业问题" in result["response"]
    assert result["reason"] == "non_homework"


def test_too_local_question_is_rejected(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "invalid",
            "intent": "ask_question",
            "reason": "too_local",
            "action": "respond_rejection",
        },
    )
    monkeypatch.setattr(
        guardrail_agent,
        "check_sync",
        lambda question: (True, "抱歉，这个问题过于本地化。"),
    )

    result = orchestrator.process_message("HKUST第一任校长是谁？", "session-local")

    assert result["category"] == "invalid"
    assert "过于本地化" in result["response"]
    assert result["reason"] == "too_local"


def test_grade_info_is_handled_before_guardrail(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "invalid",
            "intent": "grade_info",
            "reason": "grade_info",
            "action": "handle_grade_info",
        },
    )

    def fail_guardrail(question):
        raise AssertionError("guardrail should not run for grade info")

    monkeypatch.setattr(guardrail_agent, "check_sync", fail_guardrail)

    result = orchestrator.process_message("我是大一学生", "session-grade")

    assert result["intent"] == "grade_info"
    assert conversation_manager.get_grade("session-grade") == "大一"


def test_summary_request_is_handled_before_guardrail(monkeypatch):
    monkeypatch.setattr(
        triage_agent,
        "classify_sync",
        lambda question: {
            "category": "invalid",
            "intent": "summarize",
            "reason": "summarize",
            "action": "handle_summarize",
        },
    )

    def fail_guardrail(question):
        raise AssertionError("guardrail should not run for summarize")

    monkeypatch.setattr(guardrail_agent, "check_sync", fail_guardrail)
    monkeypatch.setattr(
        answer_generator,
        "generate_summary",
        lambda session_id: {"summary": "讨论了数学和历史。", "topics_discussed": ["math", "history"]},
    )

    result = orchestrator.process_message("总结我们的对话", "session-summary")

    assert result["intent"] == "summarize"
    assert "讨论了数学和历史" in result["response"]
