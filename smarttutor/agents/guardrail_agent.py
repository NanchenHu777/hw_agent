"""
Guardrail agent for homework-scope checks.
"""

from typing import Tuple

from agents.multi_model_client import multi_model_client
from app.prompts import GUARDRAIL_PROMPT, REJECTION_TEMPLATES


class GuardrailAgent:
    """Validate whether a question should be answered by SmartTutor."""

    def __init__(self):
        self.llm_client = multi_model_client
        self.system_prompt = GUARDRAIL_PROMPT
        self.rejection_templates = REJECTION_TEMPLATES

    async def check(self, question: str) -> Tuple[bool, str]:
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="guardrail",
                format_json=True,
            )
            if "error" in result:
                return self._rule_based_check(question)

            if not result.get("is_homework", False):
                category = result.get("category", "invalid")
                reasoning = result.get("reasoning", "")
                return True, self._generate_rejection_message(category, reasoning)

            return False, ""
        except Exception as exc:
            print(f"Guardrail check error: {exc}")
            return self._rule_based_check(question)

    def check_sync(self, question: str) -> Tuple[bool, str]:
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="guardrail",
                format_json=True,
            )
            if "error" in result:
                return self._rule_based_check(question)

            if not result.get("is_homework", False):
                category = result.get("category", "invalid")
                reasoning = result.get("reasoning", "")
                return True, self._generate_rejection_message(category, reasoning)

            return False, ""
        except Exception as exc:
            print(f"Guardrail check error: {exc}")
            return self._rule_based_check(question)

    def check_explicit_rules(self, question: str) -> Tuple[bool, str]:
        """Fast deterministic guardrail for already-accepted math/history questions."""
        return self._rule_based_check(question)

    def _generate_rejection_message(self, category: str, reasoning: str) -> str:
        reasoning = (reasoning or "").lower()
        if "inappropriate" in reasoning or "danger" in reasoning or "illegal" in reasoning:
            return self.rejection_templates["inappropriate"]
        if "too_local" in reasoning or "too local" in reasoning or "local" in reasoning or "niche" in reasoning:
            return self.rejection_templates["too_local"]
        if "out_of_scope" in reasoning or "out of scope" in reasoning or "outside" in reasoning:
            return self.rejection_templates["out_of_scope"]
        if "non_homework" in reasoning or "non-homework" in reasoning or "not homework" in reasoning or category == "invalid":
            return self.rejection_templates["non_homework"]
        return self.rejection_templates["default"]

    def _rule_based_check(self, question: str) -> Tuple[bool, str]:
        """Fallback checks for short, obvious prompts."""
        question_lower = question.lower()

        inappropriate = [
            "暴力",
            "违法",
            "犯罪",
            "自杀",
            "赌博",
            "吸毒",
            "火药",
            "炸弹",
            "firecracker",
            "bomb",
            "blast",
            "blast radius",
            "violence",
            "illegal",
            "crime",
            "suicide",
            "drugs",
        ]
        if any(keyword in question_lower for keyword in inappropriate):
            return True, self.rejection_templates["inappropriate"]

        out_of_scope = [
            "物理",
            "化学",
            "生物",
            "地理",
            "政治",
            "经济",
            "编程",
            "代码",
            "python",
            "physics",
            "chemistry",
            "biology",
            "geography",
            "politics",
            "economics",
            "programming",
            "code",
        ]
        if any(keyword in question_lower for keyword in out_of_scope):
            return True, self.rejection_templates["out_of_scope"]

        too_local = ["hkust", "科技大学", "校长", "本校", "小镇", "our university", "campus-specific"]
        if any(keyword in question_lower for keyword in too_local):
            return True, self.rejection_templates["too_local"]

        non_homework = [
            "旅行",
            "旅游",
            "天气",
            "电影",
            "音乐",
            "游戏",
            "伦敦",
            "怎么走",
            "怎么去",
            "最佳路线",
            "出行",
            "travel",
            "weather",
            "movie",
            "music",
            "game",
            "best route",
            "route to",
            "how do i get to",
            "how to get to",
            "trip",
        ]
        if any(keyword in question_lower for keyword in non_homework):
            return True, self.rejection_templates["non_homework"]

        return False, ""


guardrail_agent = GuardrailAgent()
