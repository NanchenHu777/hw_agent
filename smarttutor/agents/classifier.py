"""
Legacy question classifier for SmartTutor.
This module predates the active triage agent.
"""

import re
from typing import Dict, Any
from agents.llm_client import llm_client
from app.prompts import CLASSIFICATION_PROMPT


class QuestionClassifier:
    """
    Legacy question classifier.

    Note:
        The current system uses ``agents/triage_agent.py``.
        This class is retained as a fallback implementation.
    """
    
    def __init__(self):
        self.llm_client = llm_client
    
    def classify(self, question: str) -> Dict[str, Any]:
        """
        Classify a user message.
        
        Args:
            question: User message.
            
        Returns:
            Classification dictionary containing category, intent, and reason.
        """
        # Try the lightweight rule-based shortcut first.
        rule_result = self._rule_based_check(question)
        if rule_result:
            return rule_result
        
        # Fall back to an LLM classification call.
        prompt = CLASSIFICATION_PROMPT.format(user_question=question)
        
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=prompt,
                format_json=True
            )
            
            # Validate the returned payload.
            if "error" in result:
                # If JSON parsing failed, use the heuristic fallback.
                return self._fallback_classification(question)
            
            # Normalize the result into the legacy shape.
            return {
                "category": result.get("category", "invalid"),
                "intent": result.get("intent", "ask_question"),
                "reason": result.get("reason", "")
            }
            
        except Exception as e:
            print(f"分类错误: {e}")
            return self._fallback_classification(question)
    
    def _rule_based_check(self, question: str) -> Dict[str, Any]:
        """
        Rule-based classification shortcut for simple cases.
        """
        question_lower = question.lower().strip()
        
        # Detect summary requests.
        summary_keywords = ["总结", "summarize", "总结对话", "总结一下", "总结当前"]
        if any(kw in question_lower for kw in summary_keywords):
            return {
                "category": "invalid",
                "intent": "summarize",
                "reason": "用户请求总结对话"
            }
        
        # Detect grade-sharing statements.
        grade_patterns = [
            r"我是.*学生",
            r"我.*年级",
            r"大学.*年级",
            r"高中.*年级",
            r"大一|大二|大三|大四"
        ]
        for pattern in grade_patterns:
            if re.search(pattern, question_lower):
                return {
                    "category": "invalid",
                    "intent": "grade_info",
                    "reason": "用户告知年级信息"
                }
        
        return None
    
    def _fallback_classification(self, question: str) -> Dict[str, Any]:
        """
        Heuristic fallback when the LLM classification fails.
        """
        question_lower = question.lower()
        
        # Look for obvious math expressions and subject markers.
        math_patterns = [
            r"=",  # Contains an equals sign.
            r"求[xyz]",  # Chinese pattern for "solve for x/y/z".
            r"[+\-*/÷×]",  # Arithmetic operators.
            r"\d+",  # Numeric digits.
            r"等于", r"加", r"减", r"乘", r"除",  # Basic arithmetic words in Chinese.
            r"一|二|三|四|五|六|七|八|九|十",  # Chinese numerals.
            r"方程", r"函数", r"计算", r"求解", r"证明",
            r"几何", r"代数", r"微积分", r"概率", r"统计",
            r"根号", r"平方", r"角度", r"面积", r"体积",
            r"数学", r"算术", r"数", r"多少"
        ]
        
        # Look for obvious history keywords.
        history_keywords = [
            "历史", "总统", "皇帝", "战争", "革命", "朝代", "年代",
            "人物", "事件", "国家", "文明", "古代", "现代",
            "第一任", "哪国", "什么时候", "哪一年", "谁"
        ]
        
        # Score math signals.
        math_score = sum(1 for pattern in math_patterns if re.search(pattern, question))
        
        # Score history signals.
        history_score = sum(1 for kw in history_keywords if kw in question_lower)
        
        if math_score > history_score and math_score > 0:
            return {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "检测到数学相关关键词"
            }
        elif history_score > math_score and history_score > 0:
            return {
                "category": "valid_history",
                "intent": "ask_question",
                "reason": "检测到历史相关关键词"
            }
        else:
            return {
                "category": "invalid",
                "intent": "ask_question",
                "reason": "无法识别问题类型"
            }
    
    def is_valid_question(self, classification: Dict[str, Any]) -> bool:
        """Return whether the classification is one of the supported subjects."""
        return classification.get("category") in ["valid_math", "valid_history"]


# Global legacy classifier instance.
classifier = QuestionClassifier()
