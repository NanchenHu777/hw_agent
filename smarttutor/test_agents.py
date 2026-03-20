import importlib

import pytest

from agents.conversation import ConversationManager
from agents.multi_model_client import MultiModelClient


def test_conversation_manager_add_message_creates_missing_session():
    manager = ConversationManager()

    manager.add_message("session-1", "user", "hi")

    assert manager.get_history("session-1") == [{"role": "user", "content": "hi"}]


def test_conversation_manager_set_grade_creates_missing_session():
    manager = ConversationManager()

    manager.set_grade("session-2", "大一")

    assert manager.get_grade("session-2") == "大一"


def test_llm_client_module_imports_cleanly():
    module = importlib.import_module("agents.llm_client")

    assert hasattr(module, "llm_client")


def test_multi_model_client_falls_back_when_math_model_is_denied():
    class DeniedLLM:
        def invoke(self, messages):
            raise RuntimeError("team_model_access_denied: o1-mini")

    class WorkingLLM:
        def __init__(self):
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            return type("Response", (), {"content": "fallback answer"})()

    client = MultiModelClient()
    client._initialized = True
    default_llm = WorkingLLM()
    client._llms = {
        "math": DeniedLLM(),
        "default": default_llm,
    }

    result = client.chat("x+1=2", task="math")

    assert result == "fallback answer"
    assert default_llm.calls == 1
