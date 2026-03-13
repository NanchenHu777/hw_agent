"""
SmartTutor - 作业辅导智能体
Triage Agent - 使用 LangChain 实现问题分类和路由
"""

import json
from typing import Dict, Any, Optional
from agents.multi_model_client import multi_model_client
from app.prompts import TRIAGE_AGENT_PROMPT


class TriageAgent:
    """
    Triage Agent - 负责分类问题和路由到正确的处理Agent
    使用 LangChain 实现
    """
    
    def __init__(self):
        self.llm_client = multi_model_client
        self.system_prompt = TRIAGE_AGENT_PROMPT
    
    async def classify(self, question: str) -> Dict[str, Any]:
        """
        分类用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            分类结果字典
        """
        prompt = f"""请分析以下用户问题并分类：

用户问题: {question}

请以JSON格式输出分类结果：
{{
  "category": "valid_math" | "valid_history" | "invalid",
  "intent": "ask_question" | "summarize" | "grade_info" | "chit_chat",
  "reason": "分类理由",
  "action": "handoff_to_math" | "handoff_to_history" | "respond_rejection" | "handle_grade_info" | "handle_summarize"
}}"""
        
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="triage",
                format_json=True
            )
            
            if "error" in result:
                return self._fallback_classification(question)
            
            return result
            
        except Exception as e:
            print(f"Triage分类错误: {e}")
            return self._fallback_classification(question)
    
    def classify_sync(self, question: str) -> Dict[str, Any]:
        """
        同步分类用户问题（非async版本）
        """
        prompt = f"""请分析以下用户问题并分类：

用户问题: {question}

请以JSON格式输出分类结果：
{{
  "category": "valid_math" | "valid_history" | "invalid",
  "intent": "ask_question" | "summarize" | "grade_info" | "chit_chat",
  "reason": "分类理由",
  "action": "handoff_to_math" | "handoff_to_history" | "respond_rejection" | "handle_grade_info" | "handle_summarize"
}}"""
        
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=self.system_prompt,
                task="triage",
                format_json=True
            )
            
            if "error" in result:
                return self._fallback_classification(question)
            
            return result
            
        except Exception as e:
            print(f"Triage分类错误: {e}")
            return self._fallback_classification(question)
    
    def _fallback_classification(self, question: str) -> Dict[str, Any]:
        """
        回退分类策略
        使用简单的关键词匹配
        """
        question_lower = question.lower()
        
        # 简单的关键词检测
        math_keywords = ["计算", "求解", "方程", "函数", "几何", "代数", "微积分", 
                       "概率", "统计", "加", "减", "乘", "除", "等于", "求", "根号",
                       "x", "y", "z", "数学"]
        history_keywords = ["历史", "总统", "皇帝", "战争", "朝代", "年代", "人物", 
                          "事件", "第一任", "哪国", "什么时候", "谁", "哪一年", "朝代"]
        
        # 检查是否是年级信息
        grade_patterns = ["大一", "大二", "大三", "大四", "高一", "高二", "高三", 
                         "大学", "高中", "年级", "学生", "我是"]
        
        # 检查是否是总结请求
        summarize_patterns = ["总结", "summarize", "总结对话", "总结一下"]
        
        math_score = sum(1 for kw in math_keywords if kw in question_lower)
        history_score = sum(1 for kw in history_keywords if kw in question_lower)
        grade_score = sum(1 for p in grade_patterns if p in question_lower)
        summarize_score = sum(1 for p in summarize_patterns if p in question_lower)
        
        if summarize_score > 0:
            return {
                "category": "invalid",
                "intent": "summarize",
                "reason": "用户请求总结对话",
                "action": "handle_summarize"
            }
        
        if grade_score > 0 and math_score == 0 and history_score == 0:
            return {
                "category": "invalid",
                "intent": "grade_info",
                "reason": "用户告知年级信息",
                "action": "handle_grade_info"
            }
        
        if math_score > history_score and math_score > 0:
            return {
                "category": "valid_math",
                "intent": "ask_question",
                "reason": "检测到数学相关关键词",
                "action": "handoff_to_math"
            }
        elif history_score > math_score and history_score > 0:
            return {
                "category": "valid_history",
                "intent": "ask_question",
                "reason": "检测到历史相关关键词",
                "action": "handoff_to_history"
            }
        else:
            return {
                "category": "invalid",
                "intent": "ask_question",
                "reason": "无法识别问题类型",
                "action": "respond_rejection"
            }


# 全局 Triage Agent 实例
triage_agent = TriageAgent()
