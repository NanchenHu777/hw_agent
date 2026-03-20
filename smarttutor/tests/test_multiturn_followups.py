import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.answer_generator import answer_generator
from agents.conversation import conversation_manager
from agents.guardrail_agent import guardrail_agent
from agents.orchestrator import orchestrator
from agents.triage_agent import triage_agent


def setup_function():
    conversation_manager.sessions.clear()


def test_math_followup_should_continue_answering(monkeypatch):
    triage_results = iter(
        [
            {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "math_homework",
                "action": "handoff_to_math",
            },
            {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "follow_up_from_context",
                "action": "handoff_to_math",
            },
        ]
    )
    answers = iter(
        [
            "x = 1",
            "Because subtracting 1 from both sides keeps the equation balanced.",
        ]
    )

    monkeypatch.setattr(triage_agent, "classify_sync", lambda _: next(triage_results))
    monkeypatch.setattr(guardrail_agent, "check_sync", lambda _: (False, ""))
    monkeypatch.setattr(answer_generator, "generate_answer", lambda **_: next(answers))

    session_id = "math-followup"
    first = orchestrator.process_message("x+1=2", session_id)
    second = orchestrator.process_message("Why subtract 1 on both sides?", session_id)

    assert first["category"] == "valid_math"
    assert second["category"] == "valid_math"
    assert "balanced" in second["response"]


def test_history_followup_should_continue_answering(monkeypatch):
    triage_results = iter(
        [
            {
                "category": "valid_history",
                "intent": "ask_question",
                "reason": "history_homework",
                "action": "handoff_to_history",
            },
            {
                "category": "valid_history",
                "intent": "ask_question",
                "reason": "history_follow_up",
                "action": "handoff_to_history",
            },
        ]
    )
    answers = iter(
        [
            "Louis-Napoleon Bonaparte was the first president of France.",
            "He took office in 1848.",
        ]
    )

    monkeypatch.setattr(triage_agent, "classify_sync", lambda _: next(triage_results))
    monkeypatch.setattr(guardrail_agent, "check_sync", lambda _: (False, ""))
    monkeypatch.setattr(answer_generator, "generate_answer", lambda **_: next(answers))

    session_id = "history-followup"
    orchestrator.process_message("Who was the first president of France?", session_id)
    second = orchestrator.process_message("What year did he take office?", session_id)

    assert second["category"] == "valid_history"
    assert "1848" in second["response"]


def test_clarification_can_switch_from_reject_to_accept(monkeypatch):
    triage_results = iter(
        [
            {
                "category": "invalid",
                "intent": "ask_question",
                "reason": "travel_question",
                "action": "respond_rejection",
            },
            {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "distance_math_question",
                "action": "handoff_to_math",
            },
        ]
    )
    guardrail_results = iter(
        [
            (True, "Sorry, this is not a math or history homework question."),
            (False, ""),
        ]
    )

    monkeypatch.setattr(triage_agent, "classify_sync", lambda _: next(triage_results))
    monkeypatch.setattr(guardrail_agent, "check_sync", lambda _: next(guardrail_results))
    monkeypatch.setattr(
        answer_generator,
        "generate_answer",
        lambda **_: "You can compute it with a great-circle distance formula.",
    )

    session_id = "clarification-switch"
    first = orchestrator.process_message("How do I get to London?", session_id)
    second = orchestrator.process_message(
        "I mean how to calculate the straight-line distance from Hong Kong to London.",
        session_id,
    )

    assert first["category"] == "invalid"
    assert second["category"] == "valid_math"
    assert "distance" in second["response"]


def test_summary_followup_should_not_be_rejected(monkeypatch):
    triage_results = iter(
        [
            {
                "category": "invalid",
                "intent": "summarize",
                "reason": "summarize_request",
                "action": "handle_summarize",
            },
            {
                "category": "invalid",
                "intent": "summarize",
                "reason": "summary_refinement",
                "action": "handle_summarize",
            },
        ]
    )
    summaries = iter(
        [
            {"summary": "We discussed math and history.", "topics_discussed": ["math", "history"]},
            {"summary": "Math and history were discussed.", "topics_discussed": ["math", "history"]},
        ]
    )

    monkeypatch.setattr(triage_agent, "classify_sync", lambda _: next(triage_results))

    def fail_guardrail(_):
        raise AssertionError("guardrail should not run for summary follow-ups")

    monkeypatch.setattr(guardrail_agent, "check_sync", fail_guardrail)
    monkeypatch.setattr(answer_generator, "generate_summary", lambda _: next(summaries))

    session_id = "summary-followup"
    first = orchestrator.process_message("Summarize our conversation", session_id)
    second = orchestrator.process_message("Make it shorter.", session_id)

    assert first["intent"] == "summarize"
    assert second["intent"] == "summarize"
    assert "Math and history" in second["response"]


def test_primary_school_student_can_ask_advanced_math_without_rejection(monkeypatch):
    triage_results = iter(
        [
            {
                "category": "invalid",
                "intent": "grade_info",
                "reason": "grade_info",
                "action": "handle_grade_info",
            },
            {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "advanced_math_question",
                "action": "handoff_to_math",
            },
        ]
    )
    captured = {}

    monkeypatch.setattr(triage_agent, "classify_sync", lambda _: next(triage_results))
    monkeypatch.setattr(guardrail_agent, "check_sync", lambda _: (False, ""))

    def fake_generate_answer(**kwargs):
        captured["grade"] = kwargs["grade"]
        return "This topic is advanced for primary school, but here is a simple explanation."

    monkeypatch.setattr(answer_generator, "generate_answer", fake_generate_answer)

    session_id = "primary-advanced-math"
    first = orchestrator.process_message("I am a primary school student", session_id)
    second = orchestrator.process_message("Can you explain calculus?", session_id)

    assert first["intent"] == "grade_info"
    assert conversation_manager.get_grade(session_id) == "primary school student"
    assert second["category"] == "valid_math"
    assert captured["grade"] == "primary school student"
    assert "simple explanation" in second["response"]


@pytest.mark.parametrize(
    ("question", "triage_result", "guardrail_result", "expected_category"),
    [
        (
            "How do you compute the straight-line distance between two cities?",
            {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "distance_math_question",
                "action": "handoff_to_math",
            },
            (False, ""),
            "valid_math",
        ),
        (
            "What is the best route to London?",
            {
                "category": "invalid",
                "intent": "ask_question",
                "reason": "travel_question",
                "action": "respond_rejection",
            },
            (True, "Sorry, this is not a math or history homework question."),
            "invalid",
        ),
        (
            "Write Python code to solve x+1=2",
            {
                "category": "invalid",
                "intent": "ask_question",
                "reason": "programming_request",
                "action": "respond_rejection",
            },
            (True, "Sorry, this is outside math and history homework scope."),
            "invalid",
        ),
        (
            "Should I buy Bitcoin? Please use expected value.",
            {
                "category": "invalid",
                "intent": "ask_question",
                "reason": "financial_advice",
                "action": "respond_rejection",
            },
            (True, "Sorry, this is not a math or history homework question."),
            "invalid",
        ),
        (
            "Is square root of 1000 rational?",
            {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "math_homework",
                "action": "handoff_to_math",
            },
            (False, ""),
            "valid_math",
        ),
        (
            "Who was HKUST's first president?",
            {
                "category": "invalid",
                "intent": "ask_question",
                "reason": "too_local",
                "action": "respond_rejection",
            },
            (True, "Sorry, this is too local to count as a general history homework question."),
            "invalid",
        ),
    ],
)
def test_boundary_cases(monkeypatch, question, triage_result, guardrail_result, expected_category):
    monkeypatch.setattr(triage_agent, "classify_sync", lambda _: triage_result)
    monkeypatch.setattr(guardrail_agent, "check_sync", lambda _: guardrail_result)

    if expected_category != "invalid":
        monkeypatch.setattr(answer_generator, "generate_answer", lambda **_: "accepted answer")

    result = orchestrator.process_message(question, f"boundary-{expected_category}")

    assert result["category"] == expected_category
    if expected_category == "invalid":
        assert result["response"]
    else:
        assert result["response"] == "accepted answer"
