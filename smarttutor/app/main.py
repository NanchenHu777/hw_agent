"""
FastAPI entrypoint for SmartTutor.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.answer_generator import answer_generator
from agents.conversation import conversation_manager
from agents.orchestrator import orchestrator
from app.models import ChatRequest, ChatResponse, ConversationSummary


app = FastAPI(
    title="SmartTutor API",
    description="Homework tutoring API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Welcome to SmartTutor API",
        "version": "2.0.0",
        "docs": "/docs",
        "agent_system": "enabled",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="2.0.0")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or conversation_manager.create_session()

    try:
        result = orchestrator.process_message(message=request.message, session_id=session_id)
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            category=result.get("category", "invalid"),
            intent=result.get("intent", "ask_question"),
            reason=result.get("reason"),
        )
    except Exception as exc:
        error_message = f"Sorry, something went wrong. Please try again later. Error: {exc}"
        conversation_manager.add_message(session_id, "assistant", error_message)
        return ChatResponse(
            response=error_message,
            session_id=session_id,
            category="invalid",
            intent="error",
            reason="internal_error",
        )


@app.get("/conversation/{session_id}/history")
async def get_conversation_history(session_id: str):
    history = conversation_manager.get_history(session_id)
    grade = conversation_manager.get_grade(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "grade": grade,
        "message_count": len(history),
    }


@app.get("/conversation/{session_id}/summary", response_model=ConversationSummary)
async def get_conversation_summary(session_id: str):
    summary_result = answer_generator.generate_summary(session_id)
    grade = conversation_manager.get_grade(session_id)
    return ConversationSummary(
        session_id=session_id,
        summary=summary_result.get("summary", ""),
        topics_discussed=summary_result.get("topics_discussed", []),
        user_grade=grade,
    )


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    conversation_manager.clear_session(session_id)
    return {"status": "success", "message": f"Conversation {session_id} has been cleared."}


@app.get("/models")
async def list_models():
    from agents.llm_client import llm_client

    result = llm_client.test_connection()
    return {
        "provider": result.get("provider"),
        "model": llm_client.model_name,
        "status": "connected" if result.get("success") else "disconnected",
        "message": result.get("message", ""),
    }


@app.get("/agents/status")
async def agents_status():
    return {
        "status": "active",
        "agents": {
            "triage": "active",
            "math_expert": "active",
            "history_expert": "active",
            "guardrail": "active",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
