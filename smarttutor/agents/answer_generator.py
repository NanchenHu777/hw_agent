"""
SmartTutor - 作业辅导智能体
答案生成器 - 支持多模型
"""

from typing import Dict, Any, List
from agents.multi_model_client import multi_model_client
from agents.conversation import conversation_manager
from app.prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, MATH_EXPERT_PROMPT, HISTORY_EXPERT_PROMPT


class AnswerGenerator:
    """答案生成器 - 支持多模型"""
    
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
        生成问题答案
        
        Args:
            question: 用户问题
            session_id: 会话ID
            category: 问题分类
            grade: 用户年级
            
        Returns:
            生成的答案
        """
        # 获取对话历史
        history = self.conversation_manager.get_history(session_id)
        
        # 格式化年级信息
        grade_info = grade if grade else "未指定年级"
        
        # 根据分类选择模型和构建提示
        if category == "valid_math":
            system_prompt = self._build_math_prompt(grade_info)
            task = "math"  # 使用 DeepSeek
        elif category == "valid_history":
            system_prompt = self._build_history_prompt(grade_info)
            task = "history"  # 使用 Azure
        else:
            system_prompt = SYSTEM_PROMPT
            task = "default"
        
        # 如果有历史，添加上下文
        if history:
            context = self._build_context(history)
            full_question = f"{context}\n\n当前问题: {question}"
        else:
            full_question = question
        
        # 根据任务类型选择模型
        response = self.llm_client.chat(full_question, system_prompt, task=task)

        if category in {"valid_math", "valid_history"} and self._needs_simplified_retry(response):
            retry_prompt = self._build_retry_prompt(system_prompt)
            response = self.llm_client.chat(full_question, retry_prompt, task=task)

        return response
    
    def _build_math_prompt(self, grade: str) -> str:
        """构建数学提示"""
        prompt = MATH_EXPERT_PROMPT.format(grade=grade)
        prompt += "\n\n" + SYSTEM_PROMPT
        return prompt
    
    def _build_history_prompt(self, grade: str) -> str:
        """构建历史提示"""
        prompt = HISTORY_EXPERT_PROMPT.format(grade=grade)
        prompt += "\n\n" + SYSTEM_PROMPT
        return prompt

    def _build_retry_prompt(self, system_prompt: str) -> str:
        """Add a stronger instruction when the model refuses only because the topic is advanced."""
        return (
            f"{system_prompt}\n\n"
            "重要补充：不要仅仅因为用户年级较低、题目较难或内容较进阶，就直接拒绝回答。"
            "如果题目仍属于数学或历史，请先说明这是进阶内容，再用更简单的语言解释核心概念，"
            "并尽量给出最基本的答案、结论或第一步。"
            "只有在题目不属于数学/历史，或涉及不当内容时，才可以拒绝回答。"
        )

    def _needs_simplified_retry(self, response: str) -> bool:
        normalized = response.strip().lower()
        if not normalized.startswith(("抱歉", "对不起", "sorry")):
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
        ]
        refusal_markers = ["无法帮助", "不能帮助", "不能回答", "cannot help", "can't help"]

        return any(marker in response for marker in grade_or_difficulty_markers) or any(
            marker in normalized for marker in refusal_markers
        )
    
    def _build_context(self, history: List[Dict[str, str]]) -> str:
        """构建对话上下文"""
        context_messages = history[-6:]  # 只取最近6条消息
        
        context = "对话历史:\n"
        for msg in context_messages:
            role = "用户" if msg["role"] == "user" else "助手"
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    def generate_summary(self, session_id: str) -> Dict[str, Any]:
        """
        生成对话总结
        
        Args:
            session_id: 会话ID
            
        Returns:
            包含summary, topics_discussed, unanswered_questions的字典
        """
        # 获取对话历史
        history = self.conversation_manager.get_history(session_id)
        
        if not history:
            return {
                "summary": "当前对话为空。",
                "topics_discussed": [],
                "unanswered_questions": []
            }
        
        # 格式化对话历史
        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history
        ])
        
        # 调用 LLM 生成总结
        prompt = SUMMARY_PROMPT.format(conversation_history=conversation_history)
        
        result = self.llm_client.structured_output(
            message="请总结以上对话",
            system_prompt=prompt,
            task="default",
            format_json=True
        )
        
        if "error" in result:
            topics = self._extract_topics_simple(history)
            return {
                "summary": f"对话包含{len(history)}条消息。",
                "topics_discussed": topics,
                "unanswered_questions": []
            }
        
        return {
            "summary": result.get("summary", "无法生成总结"),
            "topics_discussed": result.get("topics_discussed", []),
            "unanswered_questions": result.get("unanswered_questions", [])
        }
    
    def _extract_topics_simple(self, history: List[Dict[str, str]]) -> List[str]:
        """简单提取主题"""
        topics = []
        keywords = {
            "数学": ["计算", "求解", "方程", "函数", "几何", "代数"],
            "历史": ["历史", "总统", "皇帝", "战争", "事件"]
        }
        
        for msg in history:
            content = msg.get("content", "")
            for topic, kws in keywords.items():
                if any(kw in content for kw in kws):
                    if topic not in topics:
                        topics.append(topic)
        
        return topics


# 全局答案生成器实例
answer_generator = AnswerGenerator()
