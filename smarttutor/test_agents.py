import importlib

import pytest

from agents.conversation import ConversationManager


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
