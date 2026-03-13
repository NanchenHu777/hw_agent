"""
SmartTutor - 作业辅导智能体
Agent 编排器 - 统一处理用户请求
"""

import json
from typing import Dict, Any, Optional, Tuple
from agents.llm_client import llm_client
from agents.conversation import conversation_manager
from agents.triage_agent import triage_agent
from agents.guardrail_agent import guardrail_agent
from agents.answer_generator import answer_generator
from app.prompts import REJECTION_TEMPLATES


class AgentOrchestrator:
    """
    Agent 编排器
    协调各个 Agent 处理用户请求
    """
    
    def __init__(self):
        self.llm_client = llm_client
        self.conversation_manager = conversation_manager
        self.triage_agent = triage_agent
        self.guardrail_agent = guardrail_agent
        self.answer_generator = answer_generator
    
    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息（同步版本）
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选）
            
        Returns:
            处理结果字典
        """
        # 创建或获取会话
        if not session_id:
            session_id = self.conversation_manager.create_session()
        
        # 获取用户年级
        grade = self.conversation_manager.get_grade(session_id)
        
        # 添加用户消息到历史
        self.conversation_manager.add_message(session_id, "user", message)
        
        # 第一步：使用 Triage Agent 进行分类
        classification = self.triage_agent.classify_sync(message)
        
        # 处理特殊意图
        if classification.get("action") == "handle_grade_info":
            return self._handle_grade_info(message, session_id, grade)
        
        if classification.get("action") == "handle_summarize":
            return self._handle_summarize(session_id)
        
        # 第二步：使用 Guardrail Agent 进行安全审查
        should_reject, rejection_message = self.guardrail_agent.check_sync(message)
        
        if should_reject:
            self.conversation_manager.add_message(session_id, "assistant", rejection_message)
            return {
                "response": rejection_message,
                "session_id": session_id,
                "category": "invalid",
                "intent": classification.get("intent", "ask_question"),
                "action": "rejected"
            }
        
        # 第三步：根据分类结果路由到相应的专家 Agent
        category = classification.get("category", "invalid")
        
        if category == "valid_math":
            response_text = self._handle_math(message, session_id, grade)
        elif category == "valid_history":
            response_text = self._handle_history(message, session_id, grade)
        else:
            # 未知类型，使用通用拒绝
            response_text = REJECTION_TEMPLATES["default"]
        
        # 添加助手回复到历史
        self.conversation_manager.add_message(session_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "session_id": session_id,
            "category": category,
            "intent": classification.get("intent", "ask_question"),
            "action": "answered"
        }
    
    async def process_message_async(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息（异步版本）
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选）
            
        Returns:
            处理结果字典
        """
        # 创建或获取会话
        if not session_id:
            session_id = self.conversation_manager.create_session()
        
        # 获取用户年级
        grade = self.conversation_manager.get_grade(session_id)
        
        # 添加用户消息到历史
        self.conversation_manager.add_message(session_id, "user", message)
        
        # 第一步：使用 Triage Agent 进行分类
        classification = await self.triage_agent.classify(message)
        
        # 处理特殊意图
        if classification.get("action") == "handle_grade_info":
            return self._handle_grade_info(message, session_id, grade)
        
        if classification.get("action") == "handle_summarize":
            return self._handle_summarize(session_id)
        
        # 第二步：使用 Guardrail Agent 进行安全审查
        should_reject, rejection_message = await self.guardrail_agent.check(message)
        
        if should_reject:
            self.conversation_manager.add_message(session_id, "assistant", rejection_message)
            return {
                "response": rejection_message,
                "session_id": session_id,
                "category": "invalid",
                "intent": classification.get("intent", "ask_question"),
                "action": "rejected"
            }
        
        # 第三步：根据分类结果路由到相应的专家 Agent
        category = classification.get("category", "invalid")
        
        if category == "valid_math":
            response_text = self._handle_math(message, session_id, grade)
        elif category == "valid_history":
            response_text = self._handle_history(message, session_id, grade)
        else:
            # 未知类型，使用通用拒绝
            response_text = REJECTION_TEMPLATES["default"]
        
        # 添加助手回复到历史
        self.conversation_manager.add_message(session_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "session_id": session_id,
            "category": category,
            "intent": classification.get("intent", "ask_question"),
            "action": "answered"
        }
    
    def _handle_grade_info(
        self,
        message: str,
        session_id: str,
        current_grade: Optional[str]
    ) -> Dict[str, Any]:
        """处理年级信息"""
        extracted_grade = self.conversation_manager.extract_grade_from_message(message)
        
        if extracted_grade:
            self.conversation_manager.set_grade(session_id, extracted_grade)
            response_text = f"好的，我已经记录您的年级信息为 {extracted_grade}。现在请问您有什么数学或历史作业问题需要帮助吗？"
        else:
            response_text = "好的，我已经收到您的信息。请问有什么数学或历史作业问题需要帮助吗？"
        
        self.conversation_manager.add_message(session_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": "grade_info",
            "action": "grade_info_collected"
        }
    
    def _handle_summarize(self, session_id: str) -> Dict[str, Any]:
        """处理总结请求"""
        summary_result = self.answer_generator.generate_summary(session_id)
        
        response_text = f"对话总结:\n{summary_result['summary']}\n\n讨论过的主题: {', '.join(summary_result['topics_discussed']) if summary_result['topics_discussed'] else '无'}"
        
        self.conversation_manager.add_message(session_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": "summarize",
            "action": "summarized"
        }
    
    def _handle_math(
        self,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> str:
        """处理数学问题"""
        # 使用答案生成器生成数学答案
        response = self.answer_generator.generate_answer(
            question=question,
            session_id=session_id,
            category="valid_math",
            grade=grade
        )
        return response
    
    def _handle_history(
        self,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> str:
        """处理历史问题"""
        # 使用答案生成器生成历史答案
        response = self.answer_generator.generate_answer(
            question=question,
            session_id=session_id,
            category="valid_history",
            grade=grade
        )
        return response


# 全局编排器实例
orchestrator = AgentOrchestrator()
