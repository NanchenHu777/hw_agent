"""
SmartTutor - 作业辅导智能体
对话管理器 - 管理会话历史和上下文
"""

import uuid
import time
import re
from typing import Dict, Any, List, Optional
from collections import defaultdict


class ConversationManager:
    """对话管理器 - 管理多轮对话"""
    
    def __init__(self):
        # 会话存储: {session_id: {"messages": [], "grade": None, "created_at": float}}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # 用户年级提取模式
        self.grade_patterns = [
            (r"大学\s*一\s*年\s*级|大学\s*一年级|大一", "大一"),
            (r"大学\s*二\s*年\s*级|大学\s*二年级|大二", "大二"),
            (r"大学\s*三\s*年\s*级|大学\s*三年级|大三", "大三"),
            (r"大学\s*四\s*年\s*级|大学\s*四年级|大四", "大四"),
            (r"高中\s*一\s*年\s*级|高中\s*一年级|高一", "高一"),
            (r"高中\s*二\s*年\s*级|高中\s*二年级|高二", "高二"),
            (r"高中\s*三\s*年\s*级|高中\s*三年级|高三", "高三"),
            (r"我是.*学生", "学生"),
            (r"我\s*在\s*读", "学生"),
        ]
    
    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "messages": [],
            "grade": None,
            "created_at": time.time()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.sessions[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """获取对话历史"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session["messages"]
        ]
    
    def get_grade(self, session_id: str) -> Optional[str]:
        """获取用户年级"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get("grade")
    
    def set_grade(self, session_id: str, grade: str):
        """设置用户年级"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        self.sessions[session_id]["grade"] = grade
    
    def extract_grade_from_message(self, message: str) -> Optional[str]:
        """从消息中提取年级信息"""
        message_lower = message.lower()
        
        for pattern, grade in self.grade_patterns:
            if re.search(pattern, message_lower):
                return grade
        
        return None
    
    def is_grade_info(self, message: str) -> bool:
        """检查消息是否包含年级信息"""
        return self.extract_grade_from_message(message) is not None
    
    def format_history_for_llm(self, session_id: str, max_messages: int = 10) -> str:
        """格式化对话历史供LLM使用"""
        session = self.get_session(session_id)
        if not session:
            return ""
        
        messages = session["messages"][-max_messages:]
        formatted = []
        
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """清理旧会话"""
        current_time = time.time()
        to_delete = [
            sid for sid, session in self.sessions.items()
            if current_time - session["created_at"] > max_age_seconds
        ]
        
        for sid in to_delete:
            del self.sessions[sid]


# 全局对话管理器实例
conversation_manager = ConversationManager()
