"""
Legacy guardrails module for SmartTutor.
This module predates the active guardrail agent.
"""

import re
from typing import Dict, Any
from app.prompts import REJECTION_TEMPLATES


class Guardrails:
    """
    Legacy guardrail helper used to reject invalid questions.

    Note:
        The current system uses ``agents/guardrail_agent.py``.
        This class is retained as a fallback implementation.
    """
    
    def __init__(self):
        self.rejection_templates = REJECTION_TEMPLATES
    
    def check_and_reject(self, question: str, classification: Dict[str, Any]) -> tuple[bool, str]:
        """
        Decide whether a question should be rejected.
        
        Args:
            question: User question.
            classification: Classification result.
            
        Returns:
            (should_reject, rejection_message)
        """
        # Only invalid questions need a rejection message.
        if classification.get("category") != "invalid":
            return False, ""
        
        # Retrieve the rejection reason from the classifier output.
        reason = classification.get("reason", "")
        
        # Choose the appropriate rejection template.
        rejection_message = self._get_rejection_message(question, reason)
        
        return True, rejection_message
    
    def _get_rejection_message(self, question: str, reason: str) -> str:
        """Build a rejection message from the detected reason."""
        question_lower = question.lower()
        
        # Detect non-homework prompts.
        non_homework_indicators = [
            "旅行", "旅游", "最好", "建议", "怎么办", "如何做",
            "天气", "电影", "音乐", "游戏", "吃饭", "购物"
        ]
        
        # Detect questions outside the supported subjects.
        out_of_scope_indicators = [
            "物理", "化学", "生物", "地理", "政治", "经济",
            "哲学", "心理", "编程", "代码", "电脑"
        ]
        
        # Detect overly local or niche prompts.
        too_local_indicators = [
            "hkust", "科技大学", "校长", "院系", "专业",
            "香港科技大学", "本地", "小镇"
        ]
        
        # Detect inappropriate prompts.
        inappropriate_indicators = [
            "暴力", "违法", "犯罪", "自杀", "赌博"
        ]
        
        # Match the most specific rejection reason first.
        if any(ind in question_lower for ind in inappropriate_indicators):
            return self.rejection_templates["inappropriate"]
        
        if any(ind in question_lower for ind in too_local_indicators):
            return self.rejection_templates["too_local"]
        
        if any(ind in question_lower for ind in out_of_scope_indicators):
            return self.rejection_templates["out_of_scope"]
        
        if any(ind in question_lower for ind in non_homework_indicators):
            return self.rejection_templates["non_homework"]
        
        # If the classifier already provided a reason, reuse it.
        if reason:
            return f"抱歉，我无法帮助回答这个问题，因为{reason}。如果您有数学或历史作业问题，我很乐意帮助您。"
        
        return self.rejection_templates["default"]
    
    def extract_rejection_reason(self, question: str) -> str:
        """Extract a coarse rejection label for debugging."""
        question_lower = question.lower()
        
        if any(kw in question_lower for kw in ["旅行", "旅游", "天气", "电影"]):
            return "non_homework"
        if any(kw in question_lower for kw in ["物理", "化学", "生物"]):
            return "out_of_scope"
        if any(kw in question_lower for kw in ["科技大学", "校长"]):
            return "too_local"
        
        return "unknown"


# Global legacy guardrails instance.
guardrails = Guardrails()
