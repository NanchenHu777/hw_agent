"""
SmartTutor - 作业辅导智能体
Agent 编排器 - 统一处理用户请求、支持流式输出
"""

import json
import time
from typing import Dict, Any, Optional, Tuple
from agents.llm_client import llm_client
from agents.conversation import conversation_manager
from agents.triage_agent import triage_agent
from agents.guardrail_agent import guardrail_agent
from agents.answer_generator import answer_generator
from agents.multi_model_client import multi_model_client
from app.prompts import REJECTION_TEMPLATES, WELCOME_MESSAGE


class AgentOrchestrator:
    """
    Agent 编排器
    协调各个 Agent 处理用户请求
    """

    # 流式输出超时时间（秒）
    STREAM_TIMEOUT = 60

    def __init__(self):
        self.llm_client = llm_client
        self.conversation_manager = conversation_manager
        self.triage_agent = triage_agent
        self.guardrail_agent = guardrail_agent
        self.answer_generator = answer_generator
        self.multi_model_client = multi_model_client

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

        # 检查是否是首次对话
        history = self.conversation_manager.get_history(session_id)
        if not history:
            # 发送欢迎语
            self.conversation_manager.add_message(session_id, "assistant", WELCOME_MESSAGE)
            return {
                "response": WELCOME_MESSAGE,
                "session_id": session_id,
                "action": "welcome"
            }

        # 添加用户消息到历史
        self.conversation_manager.add_message(session_id, "user", message)

        # 获取用户年级
        grade = self.conversation_manager.get_grade(session_id)

        # 第一步：使用 Triage Agent 进行分类
        classification = self.triage_agent.classify_sync(message)
        action = classification.get("action", "respond_rejection")

        # 第二步：根据意图处理
        if action == "handle_grade_info":
            return self._handle_grade_info(message, session_id, grade)

        if action == "handle_summarize":
            return self._handle_summarize(session_id)

        if action in ["handoff_to_math", "handoff_to_history"]:
            # 问题类请求，先进行安全审查
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

            # 检查是否是练习题请求
            if self.answer_generator.is_practice_request(message):
                response_text = self._handle_practice("math", message, session_id, grade)
            else:
                category = "valid_math" if action == "handoff_to_math" else "valid_history"
                response_text = self._generate_answer(message, session_id, category, grade)

            self.conversation_manager.add_message(session_id, "assistant", response_text)
            return {
                "response": response_text,
                "session_id": session_id,
                "category": classification.get("category", "invalid"),
                "intent": classification.get("intent", "ask_question"),
                "action": "answered"
            }

        # 其他情况（非具体问题），给予友好提示
        response_text = self._handle_general_help(message)
        self.conversation_manager.add_message(session_id, "assistant", response_text)
        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": classification.get("intent", "chit_chat"),
            "action": "help_suggested"
        }

    def process_message_stream(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        处理用户消息（流式版本）

        Args:
            message: 用户消息
            session_id: 会话ID（可选）

        Returns:
            (流式响应生成器, 处理结果字典)
        """
        # 创建或获取会话
        if not session_id:
            session_id = self.conversation_manager.create_session()

        # 检查是否是首次对话
        history = self.conversation_manager.get_history(session_id)
        if not history:
            welcome_msg = WELCOME_MESSAGE
            self.conversation_manager.add_message(session_id, "assistant", welcome_msg)
            return iter([welcome_msg]), {
                "response": welcome_msg,
                "session_id": session_id,
                "action": "welcome"
            }

        # 获取用户年级
        grade = self.conversation_manager.get_grade(session_id)

        # 添加用户消息到历史
        self.conversation_manager.add_message(session_id, "user", message)

        # 第一步：使用 Triage Agent 进行分类
        classification = self.triage_agent.classify_sync(message)

        # 处理特殊意图
        if classification.get("action") == "handle_grade_info":
            return self._handle_grade_info_stream(message, session_id, grade)

        if classification.get("action") == "handle_summarize":
            return self._handle_summarize_stream(session_id)

        # 第二步：使用 Guardrail Agent 进行安全审查
        should_reject, rejection_message = self.guardrail_agent.check_sync(message)

        if should_reject:
            self.conversation_manager.add_message(session_id, "assistant", rejection_message)
            return iter([rejection_message]), {
                "response": rejection_message,
                "session_id": session_id,
                "category": "invalid",
                "intent": classification.get("intent", "ask_question"),
                "action": "rejected"
            }

        # 第三步：根据分类结果路由
        category = classification.get("category", "invalid")

        if category == "valid_math":
            if self.answer_generator.is_practice_request(message):
                return self._handle_practice_stream("math", message, session_id, grade)
            else:
                return self._handle_math_stream(message, session_id, grade)
        elif category == "valid_history":
            return self._handle_history_stream(message, session_id, grade)
        else:
            response_text = REJECTION_TEMPLATES["default"]
            self.conversation_manager.add_message(session_id, "assistant", response_text)
            return iter([response_text]), {
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
        """处理用户消息（异步版本）"""
        # 创建或获取会话
        if not session_id:
            session_id = self.conversation_manager.create_session()

        # 检查是否是首次对话
        history = self.conversation_manager.get_history(session_id)
        if not history:
            self.conversation_manager.add_message(session_id, "assistant", WELCOME_MESSAGE)
            return {
                "response": WELCOME_MESSAGE,
                "session_id": session_id,
                "action": "welcome"
            }

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

        # 第三步：根据分类结果路由
        category = classification.get("category", "invalid")

        if category == "valid_math":
            if self.answer_generator.is_practice_request(message):
                response_text = self._handle_practice("math", message, session_id, grade)
            else:
                response_text = self._handle_math(message, session_id, grade)
        elif category == "valid_history":
            response_text = self._handle_history(message, session_id, grade)
        else:
            response_text = REJECTION_TEMPLATES["default"]

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

    def _handle_grade_info_stream(
        self,
        message: str,
        session_id: str,
        current_grade: Optional[str]
    ) -> Tuple[any, Dict[str, Any]]:
        """处理年级信息（流式版本）"""
        result = self._handle_grade_info(message, session_id, current_grade)
        return iter([result["response"]]), result

    def _handle_summarize(self, session_id: str) -> Dict[str, Any]:
        """处理总结请求"""
        summary_result = self.answer_generator.generate_summary(session_id)

        response_text = f"## 对话总结\n\n{summary_result['summary']}\n\n### 讨论的主题\n"
        response_text += "、".join(summary_result['topics_discussed']) if summary_result['topics_discussed'] else "无"

        if summary_result.get('unanswered_questions'):
            response_text += f"\n\n### 待解决的问题\n"
            response_text += "、".join(summary_result['unanswered_questions'])

        self.conversation_manager.add_message(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "session_id": session_id,
            "category": "invalid",
            "intent": "summarize",
            "action": "summarized"
        }

    def _handle_summarize_stream(self, session_id: str) -> Tuple[any, Dict[str, Any]]:
        """处理总结请求（流式版本）"""
        result = self._handle_summarize(session_id)
        return iter([result["response"]]), result

    def _handle_general_help(self, message: str) -> str:
        """处理通用帮助请求"""
        return (
            "我是一个数学和历史作业辅导助手。您可以：\n\n"
            "• 问我数学或历史作业问题\n"
            "• 告诉我您的年级（如\"我是大一学生\"）\n"
            "• 让我生成练习题（如\"给我出几道二次函数的练习题\"）\n"
            "• 要求总结对话（如\"总结我们的对话\"）\n\n"
            "请问有什么可以帮助您的？"
        )

    def _generate_answer(
        self,
        question: str,
        session_id: str,
        category: str,
        grade: Optional[str]
    ) -> str:
        """生成答案（统一方法）"""
        response = self.answer_generator.generate_answer(
            question=question,
            session_id=session_id,
            category=category,
            grade=grade
        )
        return response

    def _handle_math(
        self,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> str:
        """处理数学问题"""
        response = self.answer_generator.generate_answer(
            question=question,
            session_id=session_id,
            category="valid_math",
            grade=grade
        )
        return response

    def _handle_math_stream(
        self,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> Tuple[any, Dict[str, Any]]:
        """处理数学问题（流式版本）"""
        grade_info = grade if grade else "未指定年级"
        system_prompt = self.answer_generator._build_math_prompt(grade_info, question)

        history = self.conversation_manager.get_history(session_id)
        if history and len(history) >= 2:
            context = self.answer_generator._build_context(history)
            full_question = f"{context}\n\n当前问题: {question}"
        else:
            full_question = question

        def generate():
            for chunk in self.multi_model_client.chat_with_history_stream(
                messages=[{"role": "user", "content": full_question}],
                system_prompt=system_prompt,
                task="math",
                timeout=self.STREAM_TIMEOUT
            ):
                yield chunk

        response_text = self._handle_math(question, session_id, grade)
        self.conversation_manager.add_message(session_id, "assistant", response_text)

        return generate(), {
            "response": response_text,
            "session_id": session_id,
            "category": "valid_math",
            "intent": "ask_question",
            "action": "answered"
        }

    def _handle_history(
        self,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> str:
        """处理历史问题"""
        response = self.answer_generator.generate_answer(
            question=question,
            session_id=session_id,
            category="valid_history",
            grade=grade
        )
        return response

    def _handle_history_stream(
        self,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> Tuple[any, Dict[str, Any]]:
        """处理历史问题（流式版本）"""
        grade_info = grade if grade else "未指定年级"
        system_prompt = self.answer_generator._build_history_prompt(grade_info)

        history = self.conversation_manager.get_history(session_id)
        if history and len(history) >= 2:
            context = self.answer_generator._build_context(history)
            full_question = f"{context}\n\n当前问题: {question}"
        else:
            full_question = question

        def generate():
            for chunk in self.multi_model_client.chat_with_history_stream(
                messages=[{"role": "user", "content": full_question}],
                system_prompt=system_prompt,
                task="history",
                timeout=self.STREAM_TIMEOUT
            ):
                yield chunk

        response_text = self._handle_history(question, session_id, grade)
        self.conversation_manager.add_message(session_id, "assistant", response_text)

        return generate(), {
            "response": response_text,
            "session_id": session_id,
            "category": "valid_history",
            "intent": "ask_question",
            "action": "answered"
        }

    def _handle_practice(
        self,
        subject: str,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> str:
        """处理练习题请求"""
        topic = self.answer_generator.extract_topic(question) or "相关知识点"
        count = 3  # 默认生成3道题

        response = self.answer_generator.generate_practice(
            subject=subject,
            topic=topic,
            count=count,
            grade=grade
        )
        return response

    def _handle_practice_stream(
        self,
        subject: str,
        question: str,
        session_id: str,
        grade: Optional[str]
    ) -> Tuple[any, Dict[str, Any]]:
        """处理练习题请求（流式版本）"""
        response_text = self._handle_practice(subject, question, session_id, grade)
        self.conversation_manager.add_message(session_id, "assistant", response_text)

        return iter([response_text]), {
            "response": response_text,
            "session_id": session_id,
            "category": f"valid_{subject}" if subject != "history" else "valid_history",
            "intent": "ask_question",
            "action": "practice_generated"
        }


# 全局编排器实例
orchestrator = AgentOrchestrator()
