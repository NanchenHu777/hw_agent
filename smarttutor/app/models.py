"""
SmartTutor - 作业辅导智能体
数据模型定义
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class QuestionCategory(str, Enum):
    """问题分类枚举"""
    VALID_MATH = "valid_math"
    VALID_HISTORY = "valid_history"
    INVALID = "invalid"


class UserIntent(str, Enum):
    """用户意图枚举"""
    ASK_QUESTION = "ask_question"
    SUMMARIZE = "summarize"
    GRADE_INFO = "grade_info"
    CHIT_CHAT = "chit_chat"


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID")
    category: str = Field(..., description="Question category")
    intent: str = Field(..., description="User intent")
    reason: Optional[str] = Field(None, description="Classification reason")


class ConversationSummary(BaseModel):
    """对话总结模型"""
    session_id: str
    summary: str
    topics_discussed: list[str]
    user_grade: Optional[str]


class ConversationHistoryItem(BaseModel):
    """对话历史项"""
    role: str
    content: str
    timestamp: float
