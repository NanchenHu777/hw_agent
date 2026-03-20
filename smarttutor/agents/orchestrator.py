"""
Central request routing for SmartTutor.
"""

from typing import Any, Dict, Optional

from agents.answer_generator import answer_generator
from agents.conversation import conversation_manager
from agents.guardrail_agent import guardrail_agent
from agents.triage_agent import triage_agent
from app.prompts import REJECTION_TEMPLATES


class AgentOrchestrator:
    """Coordinate triage, guardrails, and subject answers."""

    def __init__(self):
        self.conversation_manager = conversation_manager
        self.triage_agent = triage_agent
        self.guardrail_agent = guardrail_agent
        self.answer_generator = answer_generator

    def process_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        session_id = session_id or self.conversation_manager.create_session()
        grade = self.conversation_manager.get_grade(session_id)

        self.conversation_manager.add_message(session_id, "user", message)
        classification = self.triage_agent.classify_sync(message)
        reason = classification.get("reason")
        action = classification.get("action")

        if action == "handle_grade_info":
            return self._handle_grade_info(message, session_id, reason)

        if action == "handle_summarize":
            return self._handle_summarize(session_id, reason)

        should_reject, rejection_message = self.guardrail_agent.check_sync(message)
        if should_reject:
            self.conversation_manager.add_message(session_id, "assistant", rejection_message)
            return {
                "response": rejection_message,
                "session_id": session_id,
                "category": "invalid",
                "intent": classification.get("intent", "ask_question"),
                "reason": reason or "guardrail_rejected",
                "action": "rejected",
            }

        category = classification.get("category", "invalid")
        if category == "valid_math":
            response_text = self._handle_math(message, session_id, grade)
        elif category == "valid_history":
            response_text = self._handle_history(message, session_id, grade)
        else:
            response_text = REJECTION_TEMPLATES["default"]

        self.conversation_manager.add_message(session_id, "assistant", response_text)
        return {
            "response": response_text,
            "session_id": session_id,
            "category": category,
            "intent": classification.get("intent", "ask_question"),
            "reason": reason,
            "action": "answered",
        }

    async def process_message_async(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = session_id or self.conversation_manager.create_session()
        grade = self.conversation_manager.get_grade(session_id)

        self.conversation_manager.add_message(session_id, "user", message)
        classification = await self.triage_agent.classify(message)
        reason = classification.get("reason")
        action = classification.get("action")

        if action == "handle_grade_info":
            return self._handle_grade_info(message, session_id, reason)

        if action == "handle_summarize":
            return self._handle_summarize(session_id, reason)

        should_reject, rejection_message = await self.guardrail_agent.check(message)
        if should_reject:
            self.conversation_manager.add_message(session_id, "assistant", rejection_message)
            return {
                "response": rejection_message,
                "session_id": session_id,
                "category": "invalid",
                "intent": classification.get("intent", "ask_question"),
                "reason": reason or "guardrail_rejected",
                "action": "rejected",
            }

        category = classification.get("category", "invalid")
        if category == "valid_math":
            response_text = self._handle_math(message, session_id, grade)
        elif category == "valid_history":
            response_text = self._handle_history(message, session_id, grade)
        else:
            response_text = REJECTION_TEMPLATES["default"]

        self.conversation_manager.add_message(session_id, "assistant", response_text)
        return {
            "response": response_text,
            "session_id": session_id,
            "category": category,
            "intent": classification.get("intent", "ask_question"),
            "reason": reason,
            "action": "answered",
        }

    def _handle_grade_info(
        self, message: str, session_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        extracted_grade = self.conversation_manager.extract_grade_from_message(message)

        if extracted_grade:
            self.conversation_manager.set_grade(session_id, extracted_grade)
            response_text = (
                f"好的，我已经记录你的年级信息：{extracted_grade}。"
                "接下来我会按这个水平回答你的数学或历史作业问题。"
            )
        else:
            response_text = "好的，我收到你的信息了。你可以继续问数学或历史作业问题。"

        self.conversation_manager.add_message(session_id, "assistant", response_text)
        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": "grade_info",
            "reason": reason or "grade_info",
            "action": "grade_info_collected",
        }

    def _handle_summarize(self, session_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        summary_result = self.answer_generator.generate_summary(session_id)
        topics = summary_result.get("topics_discussed", [])
        response_text = (
            f"对话总结:\n{summary_result.get('summary', '')}\n\n"
            f"讨论过的主题: {', '.join(topics) if topics else '无'}"
        )

        self.conversation_manager.add_message(session_id, "assistant", response_text)
        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": "summarize",
            "reason": reason or "summarize",
            "action": "summarized",
        }

    def _handle_math(self, question: str, session_id: str, grade: Optional[str]) -> str:
        return self.answer_generator.generate_answer(
            question=question,
            session_id=session_id,
            category="valid_math",
            grade=grade,
        )

    def _handle_history(self, question: str, session_id: str, grade: Optional[str]) -> str:
        return self.answer_generator.generate_answer(
            question=question,
            session_id=session_id,
            category="valid_history",
            grade=grade,
        )


orchestrator = AgentOrchestrator()
