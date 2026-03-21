"""
SmartTutor - 作业辅导智能体
增强型对话管理器 - 结构化记忆系统
支持：
- 用户画像存储（年级、偏好、学习进度）
- 知识点追踪（讨论过的知识点列表）
- 对话历史管理
- 追问意图识别
"""

import uuid
import time
import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict


class Subject(Enum):
    """学科枚举"""
    MATH = "math"
    HISTORY = "history"
    UNKNOWN = "unknown"


class MessageType(Enum):
    """消息类型"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """消息结构"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    message_type: str = "general"  # general, question, answer, practice, summary
    category: str = "unknown"  # math, history, meta
    topics: List[str] = field(default_factory=list)  # 涉及的知识点
    is_followup: bool = False  # 是否是追问
    parent_message_id: Optional[str] = None  # 父消息ID（用于追问链追踪）


@dataclass
class Topic:
    """知识点结构"""
    name: str
    subject: str
    first_mentioned: float
    last_discussed: float
    discussion_count: int = 1
    depth_level: int = 1  # 讨论深度：1=简单提及，2=有讲解，3=深度讨论
    followup_count: int = 0  # 追问次数
    difficulty_hints: List[str] = field(default_factory=list)  # 难度提示
    related_topics: List[str] = field(default_factory=list)  # 相关知识点


@dataclass
class UserProfile:
    """用户画像"""
    grade: Optional[str] = None
    preferred_subject: Optional[str] = None
    learning_gaps: List[str] = field(default_factory=list)  # 学习薄弱点
    strong_areas: List[str] = field(default_factory=list)  # 擅长领域
    interaction_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)


@dataclass
class Session:
    """会话结构"""
    session_id: str
    user_profile: UserProfile = field(default_factory=UserProfile)
    messages: List[Message] = field(default_factory=list)
    topics: Dict[str, Topic] = field(default_factory=dict)  # topic_name -> Topic
    current_topic: Optional[str] = None  # 当前讨论的主题
    current_subject: Optional[str] = None  # 当前学科
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    增强型对话管理器

    特性：
    1. 结构化记忆：用户画像、知识点追踪、讨论深度
    2. 追问识别：自动检测追问意图
    3. 上下文管理：追踪当前主题和讨论脉络
    4. 历史压缩：自动总结和压缩旧对话
    """

    # 年级正则模式
    GRADE_PATTERNS = [
        (r"大学\s*一\s*年\s*级|大学\s*一年级|大\s*一|大一", "大一"),
        (r"大学\s*二\s*年\s*级|大学\s*二年级|大\s*二|大二", "大二"),
        (r"大学\s*三\s*年\s*级|大学\s*三年级|大\s*三|大三", "大三"),
        (r"大学\s*四\s*年\s*级|大学\s*四年级|大\s*四|大四", "大四"),
        (r"研究生\s*一\s*年\s*级|研一", "研一"),
        (r"研究生\s*二\s*年\s*级|研二", "研二"),
        (r"研究生\s*三\s*年\s*级|研三", "研三"),
        (r"博士", "博士"),
        (r"高中\s*一\s*年\s*级|高中\s*一年级|高\s*一|高一", "高一"),
        (r"高中\s*二\s*年\s*级|高中\s*二年级|高\s*二|高二", "高二"),
        (r"高中\s*三\s*年\s*级|高中\s*三年级|高\s*三|高三", "高三"),
        (r"初中\s*一\s*年\s*级|初一", "初一"),
        (r"初中\s*二\s*年\s*级|初二", "初二"),
        (r"初中\s*三\s*年\s*级|初三", "初三"),
        (r"小学", "小学生"),
    ]

    # 追问关键词
    FOLLOWUP_PATTERNS = [
        # 代词类（指代前文）
        r"这", r"这个", r"它", r"那", r"那个",
        # 疑问词类
        r"为什么", r"怎么", r"如何", r"什么意思", r"为什么",
        # 扩展类
        r"还有呢", r"然后呢", r"能详细点吗", r"再", r"继续",
        r"能解释一下", r"能举个例子", r"比如", r"举例子",
        # 追问具体方面
        r"第一步", r"第二步", r"详细", r"具体",
    ]

    # 学科关键词
    SUBJECT_KEYWORDS = {
        Subject.MATH: [
            "计算", "求解", "方程", "函数", "几何", "代数",
            "微积分", "导数", "积分", "概率", "统计",
            "数列", "向量", "矩阵", "行列式", "三角函数",
            "对数", "指数", "根号", "平方", "立方",
            "加", "减", "乘", "除", "等于", "证明",
            "数学", "算术", "算一算", "算术"
        ],
        Subject.HISTORY: [
            "历史", "总统", "皇帝", "国王", "皇后",
            "战争", "革命", "事件", "年代", "时期",
            "朝代", "文明", "国家", "独立", "统一",
            "签署", "条约", "议会", "王朝", "文化"
        ]
    }

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._max_messages_per_session = 50  # 超过此数量触发压缩
        self._summary_threshold = 10  # 多少轮对话后建议总结

    # ==================== 会话管理 ====================

    def create_session(self, session_id: Optional[str] = None) -> str:
        """创建新会话"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        self.sessions[session_id] = Session(
            session_id=session_id,
            user_profile=UserProfile(),
            messages=[],
            topics={}
        )
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    # ==================== 消息管理 ====================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "general",
        category: str = "unknown",
        topics: Optional[List[str]] = None,
        is_followup: bool = False
    ):
        """添加消息到会话"""
        if session_id not in self.sessions:
            self.create_session(session_id)

        session = self.sessions[session_id]

        # 更新用户活跃时间
        session.user_profile.last_active = time.time()
        if role == "user":
            session.user_profile.interaction_count += 1

        # 创建消息
        message = Message(
            role=role,
            content=content,
            message_type=message_type,
            category=category,
            topics=topics or [],
            is_followup=is_followup
        )

        session.messages.append(message)

        # 自动更新当前主题
        if category in ["math", "history"] and topics:
            session.current_subject = category
            if topics[0]:
                session.current_topic = topics[0]

        # 触发知识点更新
        if topics and role == "assistant":
            for topic in topics:
                self._update_topic(session, topic, category)

        # 检查是否需要压缩
        if len(session.messages) > self._max_messages_per_session:
            self._compress_session(session)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """获取对话历史（简化格式）"""
        session = self.get_session(session_id)
        if not session:
            return []

        return [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages
        ]

    def get_messages(self, session_id: str, last_n: Optional[int] = None) -> List[Message]:
        """获取消息列表（完整格式）"""
        session = self.get_session(session_id)
        if not session:
            return []

        messages = session.messages
        if last_n:
            messages = messages[-last_n:]
        return messages

    # ==================== 年级管理 ====================

    def get_grade(self, session_id: str) -> Optional[str]:
        """获取用户年级"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.user_profile.grade

    def set_grade(self, session_id: str, grade: str):
        """设置用户年级"""
        if session_id not in self.sessions:
            self.create_session(session_id)

        self.sessions[session_id].user_profile.grade = grade

    def extract_grade(self, message: str) -> Optional[str]:
        """从消息中提取年级"""
        for pattern, grade in self.GRADE_PATTERNS:
            if re.search(pattern, message):
                return grade
        return None

    # ==================== 追问识别 ====================

    def is_followup(self, message: str) -> bool:
        """
        检测是否是追问
        通过模式匹配判断消息是否指向前文
        """
        message_lower = message.lower()

        # 检查是否包含追问模式
        for pattern in self.FOLLOWUP_PATTERNS:
            if re.search(pattern, message_lower):
                return True

        # 检查是否是短消息（通常追问较短）
        if len(message) < 15 and not message.endswith("？"):
            return True

        return False

    def get_followup_type(self, message: str) -> str:
        """
        获取追问类型
        - deep_dive: 深入讲解
        - clarification: 澄清疑问
        - example: 要求举例
        - continue: 继续提问
        """
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["为什么", "为什么", "原因", "原理"]):
            return "deep_dive"
        if any(kw in message_lower for kw in ["什么意思", "什么", "哪个", "怎么理解"]):
            return "clarification"
        if any(kw in message_lower for kw in ["例子", "比如", "举", "example"]):
            return "example"
        if any(kw in message_lower for kw in ["继续", "还有", "然后"]):
            return "continue"
        if any(kw in message_lower for kw in ["详细", "具体", "能"]):
            return "deep_dive"

        return "general"

    # ==================== 上下文构建 ====================

    def build_context_for_llm(
        self,
        session_id: str,
        include_profile: bool = True,
        include_topics: bool = True,
        max_messages: int = 8
    ) -> str:
        """
        构建供 LLM 使用的上下文
        """
        session = self.get_session(session_id)
        if not session:
            return ""

        context_parts = []

        # 1. 用户画像
        if include_profile and session.user_profile.grade:
            context_parts.append(f"用户年级: {session.user_profile.grade}")

        # 2. 当前主题
        if session.current_topic:
            context_parts.append(f"当前讨论主题: {session.current_topic}")
            context_parts.append(f"当前学科: {session.current_subject or '未知'}")

        # 3. 最近讨论的知识点
        if include_topics and session.topics:
            recent_topics = sorted(
                session.topics.items(),
                key=lambda x: x[1].last_discussed,
                reverse=True
            )[:3]
            topic_names = [t[0] for t in recent_topics]
            if topic_names:
                context_parts.append(f"已讨论的知识点: {', '.join(topic_names)}")

        # 4. 对话历史
        recent_messages = session.messages[-max_messages:] if session.messages else []
        if recent_messages:
            history_lines = []
            for msg in recent_messages:
                role = "用户" if msg.role == "user" else "助手"
                # 截断过长内容
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                history_lines.append(f"{role}: {content}")

            context_parts.append("\n对话历史:\n" + "\n".join(history_lines))

        return "\n\n".join(context_parts)

    # ==================== 知识点管理 ====================

    def _update_topic(self, session: Session, topic_name: str, subject: str):
        """更新知识点"""
        if topic_name in session.topics:
            topic = session.topics[topic_name]
            topic.last_discussed = time.time()
            topic.discussion_count += 1
        else:
            session.topics[topic_name] = Topic(
                name=topic_name,
                subject=subject,
                first_mentioned=time.time(),
                last_discussed=time.time()
            )

    def add_topic_depth(self, session_id: str, topic_name: str, depth_increment: int = 1):
        """增加话题深度"""
        session = self.get_session(session_id)
        if session and topic_name in session.topics:
            session.topics[topic_name].depth_level += depth_increment

    def get_topics(self, session_id: str, subject: Optional[str] = None) -> List[Topic]:
        """获取知识点列表"""
        session = self.get_session(session_id)
        if not session:
            return []

        topics = list(session.topics.values())
        if subject:
            topics = [t for t in topics if t.subject == subject]

        return sorted(topics, key=lambda t: t.last_discussed, reverse=True)

    # ==================== 学科识别 ====================

    def detect_subject(self, text: str) -> Subject:
        """检测文本涉及的主要学科"""
        text_lower = text.lower()

        math_score = sum(1 for kw in self.SUBJECT_KEYWORDS[Subject.MATH] if kw in text_lower)
        history_score = sum(1 for kw in self.SUBJECT_KEYWORDS[Subject.HISTORY] if kw in text_lower)

        if math_score > history_score:
            return Subject.MATH
        elif history_score > math_score:
            return Subject.HISTORY
        else:
            return Subject.UNKNOWN

    # ==================== 会话压缩 ====================

    def _compress_session(self, session: Session):
        """
        压缩会话历史
        将早期消息总结，保留关键信息
        """
        if len(session.messages) <= 10:
            return

        # 保留最近的消息
        keep_count = 20
        old_messages = session.messages[:-keep_count]
        recent_messages = session.messages[-keep_count:]

        # 生成压缩摘要（这里简化为保留首尾消息）
        if old_messages:
            first_msg = old_messages[0]
            last_msg = old_messages[-1]

            # 创建压缩消息
            summary = Message(
                role="system",
                content=f"[早期对话已压缩: 共{len(old_messages)}条消息, "
                       f"讨论主题: {session.current_topic or '多个主题'}]",
                message_type="summary"
            )

            # 替换为压缩后的消息列表
            session.messages = [first_msg, summary] + recent_messages

    # ==================== 总结生成 ====================

    def generate_session_summary(self, session_id: str) -> Dict[str, Any]:
        """生成会话总结"""
        session = self.get_session(session_id)
        if not session:
            return {}

        # 知识点统计
        math_topics = self.get_topics(session_id, "math")
        history_topics = self.get_topics(session_id, "history")

        # 用户画像
        profile = session.user_profile

        return {
            "session_id": session_id,
            "total_messages": len(session.messages),
            "interaction_count": profile.interaction_count,
            "grade": profile.grade,
            "math_topics": [t.name for t in math_topics[:5]],
            "history_topics": [t.name for t in history_topics[:5]],
            "current_topic": session.current_topic,
            "session_duration_minutes": int((time.time() - session.created_at) / 60),
            "deep_discussions": sum(1 for t in session.topics.values() if t.depth_level >= 3)
        }


# 全局实例
conversation_manager = ConversationManager()
