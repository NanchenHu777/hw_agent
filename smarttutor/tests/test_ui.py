from types import SimpleNamespace


def test_gradio_chat_delegates_to_orchestrator(monkeypatch):
    import ui.gradio_app as gradio_app

    calls = []

    def fake_process_message(message, session_id=None):
        calls.append((message, session_id))
        return {
            "response": "x = 1",
            "session_id": session_id or "ui-session",
            "category": "valid_math",
            "intent": "ask_question",
            "reason": "math_homework",
        }

    monkeypatch.setattr(gradio_app, "session_id", "ui-session")
    monkeypatch.setattr(
        gradio_app,
        "orchestrator",
        SimpleNamespace(process_message=fake_process_message),
        raising=False,
    )

    _, history = gradio_app.chat("x+1=2", [])

    assert calls == [("x+1=2", "ui-session")]
    assert history[-1][1] == "x = 1"
