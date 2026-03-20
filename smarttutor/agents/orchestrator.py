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
        last_response_kind = self.conversation_manager.get_last_response_kind(session_id)

        self.conversation_manager.add_message(session_id, "user", message)
        classification = self.triage_agent.classify_sync(message)
        classification = self._apply_followup_context(classification, message, last_response_kind)
        reason = classification.get("reason")
        action = classification.get("action")

        if action == "handle_grade_info":
            return self._handle_grade_info(message, session_id, reason)

        if action == "handle_summarize":
            return self._handle_summarize(session_id, reason)

        if action == "respond_chitchat" or (
            classification.get("intent") == "chit_chat"
            and self._looks_like_simple_chit_chat(message)
        ):
            return self._handle_chit_chat(message, session_id, reason)

        category = classification.get("category", "invalid")
        if category in {"valid_math", "valid_history"}:
            should_reject, rejection_message = self.guardrail_agent.check_explicit_rules(message)
        else:
            should_reject, rejection_message = self.guardrail_agent.check_sync(message)
        if should_reject:
            self.conversation_manager.set_last_response_kind(session_id, "rejected")
            self.conversation_manager.add_message(session_id, "assistant", rejection_message)
            return {
                "response": rejection_message,
                "session_id": session_id,
                "category": "invalid",
                "intent": classification.get("intent", "ask_question"),
                "reason": reason or "guardrail_rejected",
                "action": "rejected",
            }

        if category == "valid_math":
            response_text = self._handle_math(message, session_id, grade)
        elif category == "valid_history":
            response_text = self._handle_history(message, session_id, grade)
        else:
            response_text = REJECTION_TEMPLATES["default"]

        self.conversation_manager.set_last_response_kind(session_id, category if category in {"valid_math", "valid_history"} else "rejected")
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
        last_response_kind = self.conversation_manager.get_last_response_kind(session_id)

        self.conversation_manager.add_message(session_id, "user", message)
        classification = await self.triage_agent.classify(message)
        classification = self._apply_followup_context(classification, message, last_response_kind)
        reason = classification.get("reason")
        action = classification.get("action")

        if action == "handle_grade_info":
            return self._handle_grade_info(message, session_id, reason)

        if action == "handle_summarize":
            return self._handle_summarize(session_id, reason)

        if action == "respond_chitchat" or (
            classification.get("intent") == "chit_chat"
            and self._looks_like_simple_chit_chat(message)
        ):
            return self._handle_chit_chat(message, session_id, reason)

        category = classification.get("category", "invalid")
        if category in {"valid_math", "valid_history"}:
            should_reject, rejection_message = self.guardrail_agent.check_explicit_rules(message)
        else:
            should_reject, rejection_message = await self.guardrail_agent.check(message)
        if should_reject:
            self.conversation_manager.set_last_response_kind(session_id, "rejected")
            self.conversation_manager.add_message(session_id, "assistant", rejection_message)
            return {
                "response": rejection_message,
                "session_id": session_id,
                "category": "invalid",
                "intent": classification.get("intent", "ask_question"),
                "reason": reason or "guardrail_rejected",
                "action": "rejected",
            }

        if category == "valid_math":
            response_text = self._handle_math(message, session_id, grade)
        elif category == "valid_history":
            response_text = self._handle_history(message, session_id, grade)
        else:
            response_text = REJECTION_TEMPLATES["default"]

        self.conversation_manager.set_last_response_kind(session_id, category if category in {"valid_math", "valid_history"} else "rejected")
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
                f"Thanks. I've recorded your grade level as {extracted_grade}. "
                "I'll tailor future math or history answers to that level."
            )
        else:
            response_text = "Thanks. I've noted that information. You can continue with a math or history homework question."

        self.conversation_manager.set_last_response_kind(session_id, "grade_info")
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
            f"Conversation summary:\n{summary_result.get('summary', '')}\n\n"
            f"Topics discussed: {', '.join(topics) if topics else 'none'}"
        )

        self.conversation_manager.set_last_response_kind(session_id, "summarize")
        self.conversation_manager.add_message(session_id, "assistant", response_text)
        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": "summarize",
            "reason": reason or "summarize",
            "action": "summarized",
        }

    def _handle_chit_chat(
        self, message: str, session_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        response_text = self._build_chit_chat_response(message)
        self.conversation_manager.add_message(session_id, "assistant", response_text)
        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": "chit_chat",
            "reason": reason or "simple_chit_chat",
            "action": "chit_chat_responded",
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

    def _apply_followup_context(
        self,
        classification: Dict[str, Any],
        message: str,
        last_response_kind: Optional[str],
    ) -> Dict[str, Any]:
        if classification.get("category") in {"valid_math", "valid_history"}:
            return classification

        if classification.get("action") in {"handle_grade_info", "handle_summarize"}:
            return classification

        if last_response_kind not in {"valid_math", "valid_history", "summarize"}:
            return classification

        if not self.conversation_manager.looks_like_contextual_followup(message):
            return classification

        if last_response_kind == "summarize":
            return {
                "category": "invalid",
                "intent": "summarize",
                "reason": "Treated as a follow-up refinement of the previous summary request.",
                "action": "handle_summarize",
            }

        subject_name = "math" if last_response_kind == "valid_math" else "history"
        handoff_action = "handoff_to_math" if last_response_kind == "valid_math" else "handoff_to_history"
        return {
            "category": last_response_kind,
            "intent": "ask_question",
            "reason": f"Treated as a contextual follow-up to the previous {subject_name} answer.",
            "action": handoff_action,
        }

    def _build_chit_chat_response(self, message: str) -> str:
        message_lower = message.lower()

        gratitude_tokens = ["thank", "thanks", "helpful", "谢谢", "多谢"]
        greeting_tokens = ["hi", "hello", "hey", "你好"]
        farewell_tokens = ["bye", "goodbye", "see you", "再见"]

        if any(token in message_lower for token in gratitude_tokens):
            return "You're welcome."

        if any(token in message_lower for token in greeting_tokens):
            return "Hi. Feel free to ask a math or history homework question."

        if any(token in message_lower for token in farewell_tokens):
            return "Goodbye. Feel free to come back with a math or history homework question anytime."

        return "I'm here to help with math and history homework questions."

    def _looks_like_simple_chit_chat(self, message: str) -> bool:
        message_lower = message.lower().strip()
        simple_tokens = [
            "hi",
            "hello",
            "hey",
            "thanks",
            "thank you",
            "thankyou",
            "bye",
            "goodbye",
            "see you",
            "you're welcome",
            "you are welcome",
            "helpful",
            "你好",
            "谢谢",
            "多谢",
            "再见",
        ]
        return any(token in message_lower for token in simple_tokens)


orchestrator = AgentOrchestrator()
