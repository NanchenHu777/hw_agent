"""
Agent package exports for SmartTutor.
"""

# Import only lightweight dependencies here to avoid circular imports.
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
