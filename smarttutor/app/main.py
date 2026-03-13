"""
SmartTutor - 作业辅导智能体
FastAPI主入口 - 集成 Agent 系统
"""

import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.models import ChatRequest, ChatResponse, ConversationSummary
from app.config import config
from agents.orchestrator import orchestrator
from agents.conversation import conversation_manager


# 创建FastAPI应用
app = FastAPI(
    title="SmartTutor API",
    description="作业辅导智能体API - 使用 Agent 系统",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str


@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "message": "Welcome to SmartTutor API",
        "version": "2.0.0",
        "docs": "/docs",
        "agent_system": "enabled"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version="2.0.0"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口 - 使用 Agent 编排器处理用户消息
    """
    # 获取或创建会话ID
    session_id = request.session_id
    if not session_id:
        session_id = conversation_manager.create_session()
    
    try:
        # 使用编排器处理消息（同步版本）
        result = orchestrator.process_message(
            message=request.message,
            session_id=session_id
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            category=result.get("category", "invalid"),
            intent=result.get("intent", "ask_question")
        )
        
    except Exception as e:
        print(f"处理消息错误: {e}")
        # 发生错误时，返回友好的错误消息
        error_message = f"抱歉，发生了错误。请稍后重试。"
        conversation_manager.add_message(session_id, "assistant", error_message)
        
        return ChatResponse(
            response=error_message,
            session_id=session_id,
            category="invalid",
            intent="error"
        )


@app.get("/conversation/{session_id}/history")
async def get_conversation_history(session_id: str):
    """获取对话历史"""
    history = conversation_manager.get_history(session_id)
    grade = conversation_manager.get_grade(session_id)
    
    return {
        "session_id": session_id,
        "history": history,
        "grade": grade,
        "message_count": len(history)
    }


@app.get("/conversation/{session_id}/summary", response_model=ConversationSummary)
async def get_conversation_summary(session_id: str):
    """获取对话总结"""
    from agents.answer_generator import answer_generator
    
    summary_result = answer_generator.generate_summary(session_id)
    grade = conversation_manager.get_grade(session_id)
    
    return ConversationSummary(
        session_id=session_id,
        summary=summary_result.get("summary", ""),
        topics_discussed=summary_result.get("topics_discussed", []),
        user_grade=grade
    )


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """清除对话"""
    conversation_manager.clear_session(session_id)
    
    return {
        "status": "success",
        "message": f"会话 {session_id} 已清除"
    }


@app.get("/models")
async def list_models():
    """列出可用的模型"""
    from agents.llm_client import llm_client
    
    result = llm_client.test_connection()
    return {
        "provider": result.get("provider"),
        "model": llm_client.model_name,
        "status": "connected" if result.get("success") else "disconnected",
        "message": result.get("message", "")
    }


@app.get("/agents/status")
async def agents_status():
    """获取 Agent 状态"""
    return {
        "status": "active",
        "agents": {
            "triage": "active",
            "math_expert": "active",
            "history_expert": "active",
            "guardrail": "active"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
