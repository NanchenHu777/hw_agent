"""
Triage agent for routing SmartTutor requests.
"""

from typing import Any, Dict

from agents.multi_model_client import multi_model_client
from app.prompts import TRIAGE_AGENT_PROMPT


class TriageAgent:
    """Classify user input by subject and intent."""

    def __init__(self):
        self.llm_client = multi_model_client
        self.system_prompt = TRIAGE_AGENT_PROMPT

    async def classify(self, question: str) -> Dict[str, Any]:
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="triage",
                format_json=True,
            )
            return self._normalize_classification(question, result)
        except Exception as exc:
            print(f"Triage classification error: {exc}")
            return self._fallback_classification(question)

    def classify_sync(self, question: str) -> Dict[str, Any]:
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="triage",
                format_json=True,
            )
            return self._normalize_classification(question, result)
        except Exception as exc:
            print(f"Triage classification error: {exc}")
            return self._fallback_classification(question)

    def _normalize_classification(self, question: str, result: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in result:
            return self._fallback_classification(question)

        fallback = self._fallback_classification(question)
        fallback_action = fallback.get("action")
        result_action = result.get("action")
        fallback_category = fallback.get("category", "invalid")
        result_category = result.get("category", "invalid")

        if fallback_action in {"handle_grade_info", "handle_summarize"} and result_action != fallback_action:
            return fallback

        if result_category == "invalid" and fallback_category in {"valid_math", "valid_history"}:
            return fallback

        return result

    def _fallback_classification(self, question: str) -> Dict[str, Any]:
        """Keyword fallback for short, obvious cases."""
        question_lower = question.lower()

        math_keywords = [
            "计算",
            "求解",
            "方程",
            "函数",
            "几何",
            "代数",
            "微积分",
            "微分",
            "积分",
            "概率",
            "统计",
            "等于",
            "根号",
            "平方根",
            "math",
            "calculus",
            "x",
            "y",
            "z",
            "+",
            "-",
            "*",
            "/",
        ]
        history_keywords = [
            "历史",
            "总统",
            "皇帝",
            "战争",
            "朝代",
            "年代",
            "人物",
            "事件",
            "第一任",
            "谁是",
            "哪一年",
            "history",
        ]
        grade_patterns = [
            "大一",
            "大二",
            "大三",
            "大四",
            "高一",
            "高二",
            "高三",
            "小学生",
            "小学",
            "primary school",
            "elementary school",
            "年级",
            "学生",
            "我是",
        ]
        summarize_patterns = ["总结", "summarize", "总结对话", "conversation so far"]

        math_score = sum(1 for keyword in math_keywords if keyword in question_lower)
        history_score = sum(1 for keyword in history_keywords if keyword in question_lower)
        grade_score = sum(1 for keyword in grade_patterns if keyword in question_lower)
        summarize_score = sum(1 for keyword in summarize_patterns if keyword in question_lower)

        if summarize_score > 0:
            return {
                "category": "invalid",
                "intent": "summarize",
                "reason": "用户请求总结对话",
                "action": "handle_summarize",
            }

        if grade_score > 0 and math_score == 0 and history_score == 0:
            return {
                "category": "invalid",
                "intent": "grade_info",
                "reason": "用户告知年级信息",
                "action": "handle_grade_info",
            }

        if math_score > history_score and math_score > 0:
            return {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "检测到数学相关关键词",
                "action": "handoff_to_math",
            }

        if history_score > math_score and history_score > 0:
            return {
                "category": "valid_history",
                "intent": "ask_question",
                "reason": "检测到历史相关关键词",
                "action": "handoff_to_history",
            }

        return {
            "category": "invalid",
            "intent": "ask_question",
            "reason": "无法识别问题类型",
            "action": "respond_rejection",
        }


triage_agent = TriageAgent()
