"""
Conversation state management for SmartTutor.
"""

import re
import time
import uuid
from typing import Any, Dict, List, Optional


class ConversationManager:
    """Manage multi-turn sessions and lightweight user state."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.grade_patterns = [
            (r"小学生|小学\s*生|小学|primary school|elementary school", "primary school student"),
            (
                r"大学\s*一\s*年级|大学一年级|大一|first[- ]year university|first year university|university year\s*1|year\s*1 university|freshman",
                "first-year university student",
            ),
            (
                r"大学\s*二\s*年级|大学二年级|大二|second[- ]year university|second year university|university year\s*2|year\s*2 university|sophomore",
                "second-year university student",
            ),
            (
                r"大学\s*三\s*年级|大学三年级|大三|third[- ]year university|third year university|university year\s*3|year\s*3 university|junior",
                "third-year university student",
            ),
            (
                r"大学\s*四\s*年级|大学四年级|大四|fourth[- ]year university|fourth year university|university year\s*4|year\s*4 university|senior",
                "fourth-year university student",
            ),
            (
                r"高中\s*一\s*年级|高中一年级|高一|first[- ]year high school|first year high school|high school year\s*1",
                "first-year high school student",
            ),
            (
                r"高中\s*二\s*年级|高中二年级|高二|second[- ]year high school|second year high school|high school year\s*2",
                "second-year high school student",
            ),
            (
                r"高中\s*三\s*年级|高中三年级|高三|third[- ]year high school|third year high school|high school year\s*3",
                "third-year high school student",
            ),
            (r"研究生|研一|研二|研三|postgraduate|graduate student", "postgraduate student"),
            (r"博士|phd|doctoral student", "doctoral student"),
            (r"i am.*student|我是.*学生", "student"),
        ]

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session, or initialize a provided session id."""
        session_id = session_id or str(uuid.uuid4())
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "grade": None,
                "created_at": time.time(),
            }
        return session_id

    def _ensure_session(self, session_id: str) -> Dict[str, Any]:
        self.create_session(session_id)
        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str):
        session = self._ensure_session(session_id)
        session["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": time.time(),
            }
        )

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        session = self.get_session(session_id)
        if not session:
            return []

        return [{"role": msg["role"], "content": msg["content"]} for msg in session["messages"]]

    def get_grade(self, session_id: str) -> Optional[str]:
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get("grade")

    def set_grade(self, session_id: str, grade: str):
        session = self._ensure_session(session_id)
        session["grade"] = grade

    def extract_grade_from_message(self, message: str) -> Optional[str]:
        normalized_message = message.lower().strip()
        if "小学生" in message or "小学" in message:
            return "primary school student"
        if "primary school" in normalized_message or "elementary school" in normalized_message:
            return "primary school student"

        for pattern, grade in self.grade_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return grade
        return None

    def is_grade_info(self, message: str) -> bool:
        return self.extract_grade_from_message(message) is not None

    def format_history_for_llm(self, session_id: str, max_messages: int = 10) -> str:
        session = self.get_session(session_id)
        if not session:
            return ""

        lines = []
        for msg in session["messages"][-max_messages:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def clear_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        current_time = time.time()
        expired_ids = [
            session_id
            for session_id, session in self.sessions.items()
            if current_time - session["created_at"] > max_age_seconds
        ]
        for session_id in expired_ids:
            del self.sessions[session_id]


conversation_manager = ConversationManager()
