"""
SmartTutor - 作业辅导智能体
安全防护模块 - Guardrails
已重构：推荐使用 guardrail_agent 进行安全审查
"""

import re
from typing import Dict, Any
from app.prompts import REJECTION_TEMPLATES


class Guardrails:
    """
    安全防护类 - 拒绝无效问题
    
    注意：推荐使用 agents/guardrail_agent.py 中的 GuardrailAgent
    此类保留作为回退方案
    """
    
    def __init__(self):
        self.rejection_templates = REJECTION_TEMPLATES
    
    def check_and_reject(self, question: str, classification: Dict[str, Any]) -> tuple[bool, str]:
        """
        检查问题是否应该被拒绝
        
        Args:
            question: 用户问题
            classification: 分类结果
            
        Returns:
            (should_reject, rejection_message)
        """
        # 如果不是有效问题，检查是否需要拒绝
        if classification.get("category") != "invalid":
            return False, ""
        
        # 获取拒绝原因
        reason = classification.get("reason", "")
        
        # 根据原因选择拒绝模板
        rejection_message = self._get_rejection_message(question, reason)
        
        return True, rejection_message
    
    def _get_rejection_message(self, question: str, reason: str) -> str:
        """根据拒绝原因获取拒绝消息"""
        question_lower = question.lower()
        
        # 检测非作业问题
        non_homework_indicators = [
            "旅行", "旅游", "最好", "建议", "怎么办", "如何做",
            "天气", "电影", "音乐", "游戏", "吃饭", "购物"
        ]
        
        # 检测超出范围
        out_of_scope_indicators = [
            "物理", "化学", "生物", "地理", "政治", "经济",
            "哲学", "心理", "编程", "代码", "电脑"
        ]
        
        # 检测过于小众
        too_local_indicators = [
            "hkust", "科技大学", "校长", "院系", "专业",
            "香港科技大学", "本地", "小镇"
        ]
        
        # 检测不当问题
        inappropriate_indicators = [
            "暴力", "违法", "犯罪", "自杀", "赌博"
        ]
        
        # 匹配拒绝原因
        if any(ind in question_lower for ind in inappropriate_indicators):
            return self.rejection_templates["inappropriate"]
        
        if any(ind in question_lower for ind in too_local_indicators):
            return self.rejection_templates["too_local"]
        
        if any(ind in question_lower for ind in out_of_scope_indicators):
            return self.rejection_templates["out_of_scope"]
        
        if any(ind in question_lower for ind in non_homework_indicators):
            return self.rejection_templates["non_homework"]
        
        # 如果有具体原因，使用原因
        if reason:
            return f"抱歉，我无法帮助回答这个问题，因为{reason}。如果您有数学或历史作业问题，我很乐意帮助您。"
        
        return self.rejection_templates["default"]
    
    def extract_rejection_reason(self, question: str) -> str:
        """提取拒绝原因用于调试"""
        question_lower = question.lower()
        
        if any(kw in question_lower for kw in ["旅行", "旅游", "天气", "电影"]):
            return "non_homework"
        if any(kw in question_lower for kw in ["物理", "化学", "生物"]):
            return "out_of_scope"
        if any(kw in question_lower for kw in ["科技大学", "校长"]):
            return "too_local"
        
        return "unknown"


# 全局Guardrails实例
guardrails = Guardrails()
