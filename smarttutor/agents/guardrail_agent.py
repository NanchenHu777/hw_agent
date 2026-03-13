"""
SmartTutor - 作业辅导智能体
Guardrail Agent - 使用 LLM 进行安全审查
"""

from typing import Dict, Any, Tuple
from agents.multi_model_client import multi_model_client
from app.prompts import GUARDRAIL_PROMPT, REJECTION_TEMPLATES


class GuardrailAgent:
    """
    Guardrail Agent - 负责安全审查
    使用专门的 Agent 而非规则匹配
    """
    
    def __init__(self):
        self.llm_client = multi_model_client
        self.system_prompt = GUARDRAIL_PROMPT
        self.rejection_templates = REJECTION_TEMPLATES
    
    async def check(self, question: str) -> Tuple[bool, str]:
        """
        审查用户问题（异步版本）
        """
        prompt = f"""请判断以下用户问题是否为有效的作业问题：

用户问题: {question}

请以JSON格式输出判断结果：
{{
  "is_homework": true | false,
  "reasoning": "判断理由",
  "category": "math" | "history" | "invalid"
}}"""
        
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="guardrail",
                format_json=True
            )
            
            if "error" in result:
                return self._rule_based_check(question)
            
            is_homework = result.get("is_homework", False)
            
            if not is_homework:
                category = result.get("category", "invalid")
                reasoning = result.get("reasoning", "")
                message = self._generate_rejection_message(category, reasoning)
                return True, message
            
            return False, ""
            
        except Exception as e:
            print(f"Guardrail检查错误: {e}")
            return self._rule_based_check(question)
    
    def check_sync(self, question: str) -> Tuple[bool, str]:
        """
        审查用户问题（同步版本）
        """
        prompt = f"""请判断以下用户问题是否为有效的作业问题：

用户问题: {question}

请以JSON格式输出判断结果：
{{
  "is_homework": true | false,
  "reasoning": "判断理由",
  "category": "math" | "history" | "invalid"
}}"""
        
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="guardrail",
                format_json=True
            )
            
            if "error" in result:
                return self._rule_based_check(question)
            
            is_homework = result.get("is_homework", False)
            
            if not is_homework:
                category = result.get("category", "invalid")
                reasoning = result.get("reasoning", "")
                message = self._generate_rejection_message(category, reasoning)
                return True, message
            
            return False, ""
            
        except Exception as e:
            print(f"Guardrail检查错误: {e}")
            return self._rule_based_check(question)
    
    def _generate_rejection_message(self, category: str, reasoning: str) -> str:
        """根据分类生成拒绝消息"""
        if "non_homework" in reasoning.lower() or category == "invalid":
            return self.rejection_templates["non_homework"]
        if "out_of_scope" in reasoning.lower():
            return self.rejection_templates["out_of_scope"]
        if "too_local" in reasoning.lower():
            return self.rejection_templates["too_local"]
        if "inappropriate" in reasoning.lower():
            return self.rejection_templates["inappropriate"]
        return self.rejection_templates["default"]
    
    def _rule_based_check(self, question: str) -> Tuple[bool, str]:
        """规则匹配回退策略"""
        question_lower = question.lower()
        
        inappropriate = ["暴力", "违法", "犯罪", "自杀", "赌博", "吸毒"]
        if any(ind in question_lower for ind in inappropriate):
            return True, self.rejection_templates["inappropriate"]
        
        out_of_scope = ["物理", "化学", "生物", "地理", "政治", "经济", "编程", "代码"]
        if any(ind in question_lower for ind in out_of_scope):
            return True, self.rejection_templates["out_of_scope"]
        
        too_local = ["hkust", "科技大学", "校长", "小镇"]
        if any(ind in question_lower for ind in too_local):
            return True, self.rejection_templates["too_local"]
        
        non_homework = ["旅行", "旅游", "天气", "电影", "音乐", "游戏"]
        if any(ind in question_lower for ind in non_homework):
            return True, self.rejection_templates["non_homework"]
        
        return False, ""


# 全局实例
guardrail_agent = GuardrailAgent()
