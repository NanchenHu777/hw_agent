"""
Answer generation utilities for SmartTutor.
"""

from typing import Dict, Any, List
from agents.multi_model_client import multi_model_client
from agents.conversation import conversation_manager
from app.prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, MATH_EXPERT_PROMPT, HISTORY_EXPERT_PROMPT


class AnswerGenerator:
    """Generate answers and summaries with task-specific models."""
    
    def __init__(self):
        self.llm_client = multi_model_client
        self.conversation_manager = conversation_manager
    
    def generate_answer(
        self,
        question: str,
        session_id: str,
        category: str,
        grade: str = None
    ) -> str:
        """
        Generate an answer for a tutoring question.
        
        Args:
            question: User question.
            session_id: Conversation session id.
            category: Classified question category.
            grade: Stored user grade level.
            
        Returns:
            Generated answer text.
        """
        # Retrieve recent conversation history for context.
        history = self.conversation_manager.get_history(session_id)
        
        # Normalize grade information for the prompt.
        grade_info = grade if grade else "unspecified"
        
        # Choose the prompt and model family for this subject.
        if category == "valid_math":
            system_prompt = self._build_math_prompt(grade_info)
            task = "math"  # Use the math-preferred model route.
        elif category == "valid_history":
            system_prompt = self._build_history_prompt(grade_info)
            task = "history"  # Use the history-preferred model route.
        else:
            system_prompt = SYSTEM_PROMPT
            task = "default"
        
        # Include compact dialogue context when history is available.
        if history:
            context = self._build_context(history)
            full_question = f"{context}\n\nCurrent question: {question}"
        else:
            full_question = question
        
        # Route the request through the task-specific model client.
        response = self.llm_client.chat(full_question, system_prompt, task=task)

        if category in {"valid_math", "valid_history"} and self._needs_simplified_retry(response):
            retry_prompt = self._build_retry_prompt(system_prompt)
            response = self.llm_client.chat(full_question, retry_prompt, task=task)

        return response
    
    def _build_math_prompt(self, grade: str) -> str:
        """Build the system prompt for math questions."""
        prompt = MATH_EXPERT_PROMPT.format(grade=grade)
        prompt += "\n\n" + SYSTEM_PROMPT
        return prompt
    
    def _build_history_prompt(self, grade: str) -> str:
        """Build the system prompt for history questions."""
        prompt = HISTORY_EXPERT_PROMPT.format(grade=grade)
        prompt += "\n\n" + SYSTEM_PROMPT
        return prompt

    def _build_retry_prompt(self, system_prompt: str) -> str:
        """Add a stronger instruction when the model refuses only because the topic is advanced."""
        return (
            f"{system_prompt}\n\n"
            "Important: do not refuse only because the user is young or the topic is advanced. "
            "If the question is still about math or history, first say that it is advanced, then explain the core idea more simply, "
            "and try to provide at least the basic answer, conclusion, or first step. "
            "Only refuse if the question is not about math/history or is inappropriate."
        )

    def _needs_simplified_retry(self, response: str) -> bool:
        normalized = response.strip().lower()
        if not normalized.startswith(("抱歉", "对不起", "sorry", "apologies")):
            return False

        grade_or_difficulty_markers = [
            "小学生",
            "年级",
            "复杂",
            "太难",
            "超纲",
            "进阶",
            "不适合",
            "可能有些复杂",
            "beyond",
            "too advanced",
            "too difficult",
            "too complex",
            "too young",
            "grade level",
        ]
        refusal_markers = ["无法帮助", "不能帮助", "不能回答", "cannot help", "can't help"]

        return any(marker in response for marker in grade_or_difficulty_markers) or any(
            marker in normalized for marker in refusal_markers
        )
    
    def _build_context(self, history: List[Dict[str, str]]) -> str:
        """Build compact conversation context for the next model call."""
        context_messages = history[-6:]  # Keep only the most recent turns.
        
        context = "Conversation history:\n"
        for msg in context_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    def generate_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Generate a summary for the current conversation.
        
        Args:
            session_id: Conversation session id.
            
        Returns:
            Dictionary containing summary, topics_discussed, and unanswered_questions.
        """
        # Read the stored conversation history.
        history = self.conversation_manager.get_history(session_id)
        
        if not history:
            return {
                "summary": "The conversation is currently empty.",
                "topics_discussed": [],
                "unanswered_questions": []
            }
        
        # Flatten the conversation into prompt text.
        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history
        ])
        
        # Ask the model to generate a structured summary.
        prompt = SUMMARY_PROMPT.format(conversation_history=conversation_history)
        
        result = self.llm_client.structured_output(
            message="Please summarize the conversation above.",
            system_prompt=prompt,
            task="default",
            format_json=True
        )
        
        if "error" in result:
            topics = self._extract_topics_simple(history)
            return {
                "summary": f"The conversation contains {len(history)} messages.",
                "topics_discussed": topics,
                "unanswered_questions": []
            }
        
        return {
            "summary": result.get("summary", "Unable to generate a summary."),
            "topics_discussed": result.get("topics_discussed", []),
            "unanswered_questions": result.get("unanswered_questions", [])
        }
    
    def _extract_topics_simple(self, history: List[Dict[str, str]]) -> List[str]:
        """Extract coarse topic labels without another model call."""
        topics = []
        keywords = {
            "math": ["计算", "求解", "方程", "函数", "几何", "代数", "equation", "math", "solve", "calculus"],
            "history": ["历史", "总统", "皇帝", "战争", "事件", "history", "president", "war", "dynasty"],
        }
        
        for msg in history:
            content = msg.get("content", "")
            for topic, kws in keywords.items():
                if any(kw in content for kw in kws):
                    if topic not in topics:
                        topics.append(topic)
        
        return topics


# Global answer generator instance.
answer_generator = AnswerGenerator()
