"""
SmartTutor - 作业辅导智能体
答案生成器 - 支持多模型、流式输出、数学公式渲染、追问识别
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from agents.multi_model_client import multi_model_client
from agents.conversation import conversation_manager, Message
from app.prompts import (
    SYSTEM_PROMPT, SUMMARY_PROMPT,
    MATH_EXPERT_PROMPT, HISTORY_EXPERT_PROMPT,
    GRADE_ADAPTATION_PROMPT, PRACTICE_PROMPT, CONTEXT_PROMPT,
    DEEP_DIVE_PROMPT, FOLLOWUP_PROMPT
)


class AnswerGenerator:
    """答案生成器 - 支持多模型"""

    # 年级难度层次（数字越大难度越高）
    GRADE_LEVELS = {
        "小学": 1,
        "初一": 2, "初二": 3, "初三": 4,
        "高一": 5, "高二": 6, "高三": 7,
        "大一": 8, "大二": 9, "大三": 10, "大四": 11,
        "研一": 12, "研二": 13, "研三": 14, "博士": 15,
        "学生": 5,  # 默认学生
        "未指定年级": 5
    }

    # 数学知识点难度映射
    TOPIC_DIFFICULTY = {
        # 基础（适合1-4年级）
        "基础运算": 1, "加减乘除": 1, "简单方程": 2, "分数": 2,
        # 初中（5-7年级）
        "一元一次方程": 4, "一元二次方程": 5, "几何基础": 4, "三角形": 4,
        "函数基础": 5, "一次函数": 5, "二次函数": 6,
        # 高中（6-9年级）
        "三角函数": 6, "对数": 6, "数列": 7, "极限": 7,
        # 大学（8+年级）
        "微积分": 8, "导数": 8, "积分": 8, "微分方程": 9,
        "线性代数": 9, "矩阵": 9, "概率统计": 7,
        "Peano算术": 10, "实变函数": 11, "泛函分析": 12
    }

    def __init__(self):
        self.llm_client = multi_model_client
        self.conversation_manager = conversation_manager

    def generate_answer(
        self,
        question: str,
        session_id: str,
        category: str,
        grade: str = None,
        is_followup: bool = False,
        followup_type: str = "general"
    ) -> str:
        """
        生成问题答案

        Args:
            question: 用户问题
            session_id: 会话ID
            category: 问题分类
            grade: 用户年级
            is_followup: 是否是追问
            followup_type: 追问类型 (deep_dive, clarification, example, continue, general)
        """
        grade_info = grade if grade else "未指定年级"

        # 检测是否是追问
        if not is_followup:
            is_followup = self.conversation_manager.is_followup(question)
            followup_type = self.conversation_manager.get_followup_type(question)

        # 构建系统提示
        if category == "valid_math":
            system_prompt = self._build_math_prompt(grade_info, question, is_followup, followup_type)
            task = "math"
        elif category == "valid_history":
            system_prompt = self._build_history_prompt(grade_info, is_followup, followup_type)
            task = "history"
        else:
            system_prompt = SYSTEM_PROMPT
            task = "default"

        # 构建上下文（使用增强的记忆系统）
        context = self._build_context(session_id, question, is_followup, followup_type)

        if context:
            full_question = f"{context}\n\n当前问题: {question}"
        else:
            full_question = question

        # 如果是追问，添加追问处理提示
        if is_followup:
            full_question = self._add_followup_guidance(full_question, followup_type, session_id)

        response = self.llm_client.chat(
            full_question,
            system_prompt,
            task=task
        )

        # 渲染数学公式
        response = self._render_math_formulas(response)

        # 更新知识点追踪
        if category == "valid_math":
            self._extract_and_track_topics(session_id, question, "math")
        elif category == "valid_history":
            self._extract_and_track_topics(session_id, question, "history")

        return response

    def _build_math_prompt(
        self,
        grade: str,
        question: str = "",
        is_followup: bool = False,
        followup_type: str = "general"
    ) -> str:
        """构建数学提示（增强年级适配和追问支持）"""
        prompt = MATH_EXPERT_PROMPT.format(grade=grade)
        prompt += "\n\n" + SYSTEM_PROMPT

        # 添加年级难度提示
        grade_level = self._get_grade_level(grade)
        difficulty_hint = self._analyze_question_difficulty(question, grade_level)
        if difficulty_hint:
            prompt += f"\n\n## 难度提示\n{difficulty_hint}"

        # 如果是追问，添加追问处理提示
        if is_followup and followup_type != "general":
            prompt += f"\n\n## 追问处理\n{FOLLOWUP_PROMPT.format(followup_type=followup_type)}"

        return prompt

    def _build_history_prompt(
        self,
        grade: str,
        is_followup: bool = False,
        followup_type: str = "general"
    ) -> str:
        """构建历史提示"""
        prompt = HISTORY_EXPERT_PROMPT.format(grade=grade)
        prompt += "\n\n" + SYSTEM_PROMPT

        # 如果是追问，添加追问处理提示
        if is_followup and followup_type != "general":
            prompt += f"\n\n## 追问处理\n{FOLLOWUP_PROMPT.format(followup_type=followup_type)}"

        return prompt

    def _add_followup_guidance(
        self,
        question: str,
        followup_type: str,
        session_id: str
    ) -> str:
        """添加追问处理指导"""
        guidance = ""

        if followup_type == "deep_dive":
            guidance = "\n\n[追问类型：深度讲解] 请详细解释概念的原理和推导过程。"
        elif followup_type == "clarification":
            guidance = "\n\n[追问类型：澄清疑问] 请用更简单易懂的方式重新解释。"
        elif followup_type == "example":
            guidance = "\n\n[追问类型：举例说明] 请提供具体的例子来帮助理解。"
        elif followup_type == "continue":
            guidance = "\n\n[追问类型：继续深入] 请继续讲解相关知识点或下一个步骤。"
        elif followup_type == "general":
            # 获取最后一条助手回复作为上下文
            messages = self.conversation_manager.get_messages(session_id, last_n=4)
            if messages and messages[-1].role == "assistant":
                guidance = "\n\n[追问] 请结合上一条回答继续回应。"
            else:
                guidance = "\n\n[追问] 请继续回答。"

        return question + guidance

    def _build_context(
        self,
        session_id: str,
        current_question: str = "",
        is_followup: bool = False,
        followup_type: str = "general"
    ) -> str:
        """
        构建对话上下文
        使用增强的记忆系统
        """
        # 使用新的上下文构建方法
        context = self.conversation_manager.build_context_for_llm(
            session_id=session_id,
            include_profile=True,
            include_topics=True,
            max_messages=10 if is_followup else 6
        )

        # 如果是追问，添加更多历史上下文
        if is_followup:
            messages = self.conversation_manager.get_messages(session_id, last_n=6)
            if messages:
                context_parts = [context] if context else []
                context_parts.append("\n=== 最近的对话 ===")
                for msg in messages:
                    role = "用户" if msg.role == "user" else "助手"
                    content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
                    context_parts.append(f"{role}: {content}")
                context = "\n\n".join(context_parts)

        return context

    def _extract_and_track_topics(self, session_id: str, question: str, subject: str):
        """提取并追踪知识点"""
        # 简单的知识点提取（后续可以接入更智能的提取）
        math_topics = ["方程", "函数", "几何", "代数", "微积分", "导数", "积分",
                       "概率", "统计", "三角函数", "数列", "极限", "矩阵"]
        history_topics = ["总统", "皇帝", "战争", "革命", "事件", "朝代", "条约"]

        topics = math_topics if subject == "math" else history_topics
        found_topics = [t for t in topics if t in question]

        for topic in found_topics:
            session = self.conversation_manager.get_session(session_id)
            if session and topic in session.topics:
                session.topics[topic].discussion_count += 1
                session.topics[topic].last_discussed = __import__('time').time()

    def generate_deep_dive(
        self,
        topic: str,
        session_id: str,
        category: str,
        grade: str = None
    ) -> str:
        """
        生成深度讲解

        Args:
            topic: 要深入讲解的主题
            session_id: 会话ID
            category: 学科分类
            grade: 用户年级
        """
        grade_info = grade if grade else "未指定年级"

        # 构建深度讲解提示
        deep_prompt = DEEP_DIVE_PROMPT.format(
            topic=topic,
            grade=grade_info,
            category=category
        )

        # 获取上下文
        context = self._build_context(session_id)
        full_question = f"{context}\n\n请深入讲解主题: {topic}" if context else f"请深入讲解主题: {topic}"

        response = self.llm_client.chat(
            full_question,
            deep_prompt,
            task=category
        )

        # 渲染数学公式
        response = self._render_math_formulas(response)

        # 更新知识点深度
        self.conversation_manager.add_topic_depth(session_id, topic, depth_increment=2)

        return response

    def _get_grade_level(self, grade: str) -> int:
        """获取年级难度等级"""
        for key, level in self.GRADE_LEVELS.items():
            if key in grade:
                return level
        return 5  # 默认中等难度

    def _analyze_question_difficulty(self, question: str, grade_level: int) -> str:
        """分析问题难度并给出提示"""
        if not question:
            return ""

        question_lower = question.lower()

        # 检测问题中的知识点
        for topic, topic_level in self.TOPIC_DIFFICULTY.items():
            if topic in question_lower:
                if topic_level < grade_level - 2:
                    return f"【提示】这个问题涉及的 '{topic}' 是基础知识，难度较低，适合巩固基础。"
                elif topic_level > grade_level + 2:
                    return f"【提示】这个问题涉及的 '{topic}' 难度较高，可能超出当前年级的范围。我会给出概要解释。"

        return ""

    def _render_math_formulas(self, text: str) -> str:
        """渲染数学公式"""
        text = re.sub(r'\$\$(.+?)\$\$', r'$$\1$$', text)

        # 修复分数格式
        fraction_pattern = r'\(([^)]+)\)/(\w+)'
        text = re.sub(fraction_pattern, r'\\frac{\1}{\2}', text)

        # 确保乘号和除号正确显示
        text = text.replace('*', ' × ')

        return text

    def generate_practice(
        self,
        subject: str,
        topic: str,
        count: int = 3,
        grade: str = None
    ) -> str:
        """生成练习题"""
        grade_info = grade if grade else "未指定年级"

        prompt = PRACTICE_PROMPT.format(
            subject=subject,
            topic=topic,
            count=count,
            grade=grade_info
        )

        response = self.llm_client.chat(
            f"请生成{count}道关于'{topic}'的练习题",
            system_prompt=prompt,
            task=subject
        )

        response = self._render_math_formulas(response)
        return response

    def is_practice_request(self, question: str) -> bool:
        """检测是否是练习题请求"""
        practice_keywords = [
            "练习", "练习题", "题目", "作业题", "做题",
            "practice", "exercise", "problems",
            "给我出", "生成", "出几道", "几道题"
        ]
        question_lower = question.lower()
        return any(kw in question_lower for kw in practice_keywords)

    def extract_topic(self, question: str) -> Optional[str]:
        """从问题中提取知识点"""
        patterns = [
            r"关于(.+?)的练习",
            r"(.+?)的练习题",
            r"关于(.+?)的",
            r"生成(.+?)的练习",
            r"(.+?)相关",
        ]

        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                return match.group(1).strip()

        return None

    def generate_summary(self, session_id: str) -> Dict[str, Any]:
        """生成对话总结"""
        # 使用增强的总结方法
        summary_data = self.conversation_manager.generate_session_summary(session_id)

        # 获取对话历史
        history = self.conversation_manager.get_history(session_id)

        if not history:
            return {
                "summary": "当前对话为空。",
                "topics_discussed": [],
                "unanswered_questions": [],
                "learning_progress": {}
            }

        # 调用 LLM 生成文字总结
        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history
        ])

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
                "unanswered_questions": [],
                "learning_progress": summary_data
            }

        return {
            "summary": result.get("summary", "无法生成总结"),
            "topics_discussed": result.get("topics_discussed", []),
            "unanswered_questions": result.get("unanswered_questions", []),
            "learning_progress": summary_data
        }

    def _extract_topics_simple(self, history: List[Dict[str, str]]) -> List[str]:
        """简单提取主题"""
        topics = []
        keywords = {
            "数学": ["计算", "求解", "方程", "函数", "几何", "代数", "微积分", "概率"],
            "历史": ["历史", "总统", "皇帝", "战争", "事件", "朝代"]
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
