"""
SmartTutor - 作业辅导智能体
Gradio Web UI - 使用 LangChain
"""

import gradio as gr
import sys
import os
from typing import Tuple, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入 Agent
from agents.triage_agent import triage_agent
from agents.guardrail_agent import guardrail_agent
from agents.answer_generator import answer_generator
from agents.conversation import conversation_manager


# 全局状态
session_id: Optional[str] = None


def init_session() -> str:
    """初始化会话"""
    global session_id
    session_id = conversation_manager.create_session()
    return session_id


def chat(message: str, history: List) -> Tuple[str, List]:
    """处理聊天消息"""
    global session_id
    
    if not message.strip():
        return "", history
    
    if history is None:
        history = []
    
    # 初始化会话
    if session_id is None:
        session_id = init_session()
    
    # 添加用户消息到历史
    history.append([message, "正在思考..."])
    
    try:
        # 1. Guardrail 检查
        should_reject, reject_msg = guardrail_agent.check_sync(message)
        
        if should_reject:
            history[-1][1] = reject_msg
            conversation_manager.add_message(session_id, "user", message)
            conversation_manager.add_message(session_id, "assistant", reject_msg)
            return "", history
        
        # 2. Triage 分类
        classification = triage_agent.classify_sync(message)
        action = classification.get("action", "respond_rejection")
        
        if action == "handle_grade_info":
            # 提取年级信息
            grade = _extract_grade(message)
            conversation_manager.set_grade(session_id, grade)
            response = f"好的，我已经记录您的年级信息为：{grade}。请问有什么数学或历史作业问题需要帮助？"
            history[-1][1] = response
            conversation_manager.add_message(session_id, "user", message)
            conversation_manager.add_message(session_id, "assistant", response)
            
        elif action == "handle_summarize":
            # 生成总结
            result = answer_generator.generate_summary(session_id)
            response = f"## 对话总结\n\n{result.get('summary', '无法生成总结')}\n\n### 讨论的主题\n"
            response += "、".join(result.get('topics_discussed', [])) or "无"
            history[-1][1] = response
            conversation_manager.add_message(session_id, "user", message)
            conversation_manager.add_message(session_id, "assistant", response)
            
        elif action in ["handoff_to_math", "handoff_to_history"]:
            # 获取年级
            grade = conversation_manager.get_grade(session_id)
            category = "valid_math" if action == "handoff_to_math" else "valid_history"
            
            # 生成答案
            response = answer_generator.generate_answer(message, session_id, category, grade)
            history[-1][1] = response
            conversation_manager.add_message(session_id, "user", message)
            conversation_manager.add_message(session_id, "assistant", response)
            
        else:
            # 无效问题
            response = "抱歉，我无法帮助回答这个问题。我只擅长数学和历史作业问题。"
            history[-1][1] = response
            conversation_manager.add_message(session_id, "user", message)
            conversation_manager.add_message(session_id, "assistant", response)
        
    except Exception as e:
        history[-1][1] = f"发生错误: {str(e)}"
    
    return "", history


def _extract_grade(message: str) -> str:
    """从消息中提取年级信息"""
    message_lower = message.lower()
    
    grade_patterns = {
        "大一": "大一",
        "大二": "大二", 
        "大三": "大三",
        "大四": "大四",
        "研一": "研一",
        "研二": "研二",
        "研三": "研三",
        "博士": "博士生",
        "高一": "高一",
        "高二": "高二",
        "高三": "高三",
        "高一": "高一",
    }
    
    for pattern, grade in grade_patterns.items():
        if pattern in message:
            return grade
    
    return "未指定年级"


def clear_history() -> Tuple[str, List]:
    """清除对话历史"""
    global session_id
    session_id = init_session()
    return "", []


def greet() -> str:
    """欢迎语"""
    return "欢迎使用 SmartTutor！我是您的作业辅导助手。我可以帮助您解答数学和历史作业问题。请告诉我您的问题是什么？"


# 创建Gradio界面
with gr.Blocks(title="SmartTutor") as demo:
    gr.Markdown("# SmartTutor - 作业辅导智能体")
    gr.Markdown("帮助您解答数学和历史作业问题")
    
    with gr.Row():
        chatbot = gr.Chatbot(label="对话历史", height=500)
    
    with gr.Row():
        msg_input = gr.Textbox(
            label="输入问题",
            placeholder="请输入您的数学或历史作业问题...",
            scale=4
        )
    
    with gr.Row():
        submit_btn = gr.Button("发送", variant="primary")
        clear_btn = gr.Button("清除")
    
    gr.Markdown("---")
    gr.Markdown("### 示例问题")
    gr.Markdown("- 数学: x + 1 = 2，求 x")
    gr.Markdown("- 数学: 求根号1000是否是有理数")
    gr.Markdown("- 历史: 谁是法国第一任总统？")
    gr.Markdown("- 历史: 香港科技大学第一任校长是谁？")
    gr.Markdown("- 告诉我你的年级（如：我是大一学生）")
    gr.Markdown("- 总结对话")
    
    # 事件绑定
    submit_btn.click(chat, [msg_input, chatbot], [msg_input, chatbot])
    msg_input.submit(chat, [msg_input, chatbot], [msg_input, chatbot])
    clear_btn.click(clear_history, outputs=[msg_input, chatbot])


if __name__ == "__main__":
    # 初始化会话
    init_session()
    
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7861, 
        show_api=False,
        share=False
    )
