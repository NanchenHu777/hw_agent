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
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str = Field(..., description="助手回复")
    session_id: str = Field(..., description="会话ID")
    category: str = Field(..., description="问题分类")
    intent: str = Field(..., description="用户意图")
    reason: Optional[str] = Field(None, description="分类理由")


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
