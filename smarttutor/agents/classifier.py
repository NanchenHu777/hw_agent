"""
SmartTutor - 作业辅导智能体
问题分类器 - 使用LLM进行Zero-shot分类
已重构：推荐使用 triage_agent 进行分类
"""

import re
from typing import Dict, Any
from agents.llm_client import llm_client
from app.prompts import CLASSIFICATION_PROMPT


class QuestionClassifier:
    """
    问题分类器
    
    注意：推荐使用 agents/triage_agent.py 中的 TriageAgent
    此类保留作为回退方案
    """
    
    def __init__(self):
        self.llm_client = llm_client
    
    def classify(self, question: str) -> Dict[str, Any]:
        """
        分类用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            分类结果字典，包含category, intent, reason
        """
        # 首先进行规则匹配（快速路径）
        rule_result = self._rule_based_check(question)
        if rule_result:
            return rule_result
        
        # 使用LLM进行分类
        prompt = CLASSIFICATION_PROMPT.format(user_question=question)
        
        try:
            result = self.llm_client.structured_output(
                message=question,
                system_prompt=prompt,
                format_json=True
            )
            
            # 验证返回结果
            if "error" in result:
                # 如果LLM返回失败，回退到默认分类
                return self._fallback_classification(question)
            
            # 规范化输出
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
        基于规则的问题分类检查（快速路径）
        处理常见的简单情况
        """
        question_lower = question.lower().strip()
        
        # 检查是否是总结请求
        summary_keywords = ["总结", "summarize", "总结对话", "总结一下", "总结当前"]
        if any(kw in question_lower for kw in summary_keywords):
            return {
                "category": "invalid",
                "intent": "summarize",
                "reason": "用户请求总结对话"
            }
        
        # 检查是否在告知年级
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
        回退分类策略
        当LLM分类失败时使用
        """
        question_lower = question.lower()
        
        # 检查是否包含数学表达式模式
        math_patterns = [
            r"=",  # 包含等号
            r"求[xyz]",  # 求x, 求y, 求z
            r"[+\-*/÷×]",  # 运算符
            r"\d+",  # 数字
            r"等于", r"加", r"减", r"乘", r"除",  # 基础运算
            r"一|二|三|四|五|六|七|八|九|十",  # 中文数字
            r"方程", r"函数", r"计算", r"求解", r"证明",
            r"几何", r"代数", r"微积分", r"概率", r"统计",
            r"根号", r"平方", r"角度", r"面积", r"体积",
            r"数学", r"算术", r"数", r"多少"
        ]
        
        # 明显的历史关键词
        history_keywords = [
            "历史", "总统", "皇帝", "战争", "革命", "朝代", "年代",
            "人物", "事件", "国家", "文明", "古代", "现代",
            "第一任", "哪国", "什么时候", "哪一年", "谁"
        ]
        
        # 检查数学模式
        math_score = sum(1 for pattern in math_patterns if re.search(pattern, question))
        
        # 检查历史关键词
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
        """检查是否为有效问题"""
        return classification.get("category") in ["valid_math", "valid_history"]


# 全局分类器实例
classifier = QuestionClassifier()
