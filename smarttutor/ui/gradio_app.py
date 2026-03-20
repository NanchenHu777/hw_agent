"""
Gradio UI for SmartTutor.
"""

import os
import sys
from typing import List, Optional, Tuple

try:
    import gradio as gr
except ImportError:  # pragma: no cover - optional for test environments
    gr = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.conversation import conversation_manager
from agents.orchestrator import orchestrator


session_id: Optional[str] = None


def init_session() -> str:
    global session_id
    session_id = conversation_manager.create_session()
    return session_id


def chat(message: str, history: List) -> Tuple[str, List]:
    global session_id

    if not message.strip():
        return "", history

    history = history or []
    if session_id is None:
        session_id = init_session()

    history.append([message, "正在思考..."])

    try:
        result = orchestrator.process_message(message=message, session_id=session_id)
        session_id = result.get("session_id", session_id)
        history[-1][1] = result["response"]
    except Exception as exc:
        history[-1][1] = f"发生错误: {exc}"

    return "", history


def clear_history() -> Tuple[str, List]:
    init_session()
    return "", []


def greet() -> str:
    return "欢迎使用 SmartTutor。我可以帮助你解答数学和历史作业问题。"


def build_demo():
    if gr is None:
        raise RuntimeError("gradio is not installed")

    with gr.Blocks(title="SmartTutor") as demo:
        gr.Markdown("# SmartTutor")
        gr.Markdown("帮助你解答数学和历史作业问题")

        chatbot = gr.Chatbot(label="对话历史", height=500)
        msg_input = gr.Textbox(
            label="输入问题",
            placeholder="例如：x+1=2，谁是法国第一任总统？",
        )

        with gr.Row():
            submit_btn = gr.Button("发送", variant="primary")
            clear_btn = gr.Button("清除")

        gr.Markdown("### 示例问题")
        gr.Markdown("- x+1=2")
        gr.Markdown("- 谁是法国第一任总统？")
        gr.Markdown("- 我是大一学生")
        gr.Markdown("- 总结我们的对话")

        submit_btn.click(chat, [msg_input, chatbot], [msg_input, chatbot])
        msg_input.submit(chat, [msg_input, chatbot], [msg_input, chatbot])
        clear_btn.click(clear_history, outputs=[msg_input, chatbot])

    return demo


demo = build_demo() if gr is not None else None


if __name__ == "__main__":
    if demo is None:
        raise SystemExit("gradio is not installed")

    init_session()
    demo.launch(server_name="0.0.0.0", server_port=7861, show_api=False, share=False)
