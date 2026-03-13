"""
SmartTutor - 作业辅导智能体
Agent 模块
"""

# 只导入必要的模块，避免循环依赖
from agents.conversation import conversation_manager

__all__ = [
    "multi_model_client", 
    "conversation_manager",
    "orchestrator",
]

def __getattr__(name):
    if name == "multi_model_client":
        from agents.multi_model_client import multi_model_client
        return multi_model_client
    if name == "orchestrator":
        from agents.orchestrator import orchestrator
        return orchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
