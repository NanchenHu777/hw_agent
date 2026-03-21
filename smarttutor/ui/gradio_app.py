"""
SmartTutor - 作业辅导智能体
Gradio Web UI - 增强版：支持流式输出、数学公式渲染、追问识别、输出审查
"""

import gradio as gr
import sys
import os
import re
from typing import Tuple, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入 Agent
from agents.triage_agent import triage_agent
from agents.guardrail_agent import guardrail_agent
from agents.answer_generator import answer_generator
from agents.conversation import conversation_manager
from agents.multi_model_client import multi_model_client
from agents.output_review_agent import output_review_agent
from app.prompts import WELCOME_MESSAGE


# 全局状态
session_id: Optional[str] = None


def init_session() -> str:
    """初始化会话"""
    global session_id
    session_id = conversation_manager.create_session()
    return session_id


def render_math(text: str) -> str:
    """
    渲染数学公式为 Markdown 格式
    """
    # 修复常见的 LaTeX 语法问题
    text = text.replace('*', ' × ')
    text = text.replace('pi', 'π')
    text = text.replace('Pi', 'π')
    text = text.replace('theta', 'θ')
    text = text.replace('alpha', 'α')
    text = text.replace('beta', 'β')
    text = text.replace('gamma', 'γ')
    text = text.replace('delta', 'δ')
    text = text.replace('lambda', 'λ')
    text = text.replace('sigma', 'σ')
    text = text.replace('omega', 'ω')

    # 修复分数格式
    fraction_pattern = r'\(([^)]+)\)/(\w+)'
    text = re.sub(fraction_pattern, r'\\frac{\1}{\2}', text)

    # 修复上标格式 (x^2 -> x²)
    text = re.sub(r'(\w)\^(\d+)', r'\1<sup>\2</sup>', text)
    text = re.sub(r'(\w)\^\{([^}]+)\}', r'\1<sup>\2</sup>', text)

    # 修复下标格式
    text = re.sub(r'(\w)_(\d+)', r'\1<sub>\2</sub>', text)
    text = re.sub(r'(\w)_\{([^}]+)\}', r'\1<sub>\2</sub>', text)

    # 修复根号
    text = re.sub(r'sqrt\(([^)]+)\)', r'√\1', text)
    text = re.sub(r'√(\d+)', r'√\1', text)

    return text


def is_system_request(message: str) -> bool:
    """
    检测是否是系统功能请求
    这些请求不应该被 Guardrail 拒绝
    """
    message_lower = message.lower()

    # 功能关键词
    feature_keywords = [
        # 年级相关
        "年级", "学生", "大一", "大二", "大三", "大四",
        "高一", "高二", "高三", "初一", "初二", "初三",
        "研一", "研二", "研三", "博士", "小学",
        # 总结相关
        "总结", "summarize", "概括", "回顾",
        # 练习题相关
        "练习", "练习题", "题目", "作业题",
        "practice", "exercise", "出几道", "给我出",
        # 系统命令
        "帮助", "help", "怎么用", "功能",
    ]

    return any(kw in message_lower for kw in feature_keywords)


def process_message(message: str, history: List) -> Tuple[str, List]:
    """处理聊天消息（增强版：支持追问识别和输出审查）"""
    global session_id

    if not message.strip():
        return "", history

    if history is None:
        history = []

    # 初始化会话
    if session_id is None:
        session_id = conversation_manager.create_session()
        # 首次会话，添加欢迎语
        history.append([None, WELCOME_MESSAGE])
        conversation_manager.add_message(session_id, "assistant", WELCOME_MESSAGE)

    # 添加用户消息到历史
    history.append([message, ""])

    try:
        # 1. 检测是否是追问
        is_followup = conversation_manager.is_followup(message)
        followup_type = conversation_manager.get_followup_type(message)

        # 2. 【优先】检测是否是练习题请求（功能请求，不走 Triage）
        if answer_generator.is_practice_request(message):
            topic = answer_generator.extract_topic(message)
            subject = conversation_manager.detect_subject(message)
            subject_str = "math" if subject.value == "math" else "history"
            grade = conversation_manager.get_grade(session_id)

            response = answer_generator.generate_practice(
                subject=subject_str,
                topic=topic or "相关知识点",
                count=3,
                grade=grade
            )

            history[-1][1] = response
            conversation_manager.add_message(
                session_id, "user", message,
                message_type="practice",
                category=subject_str
            )
            conversation_manager.add_message(
                session_id, "assistant", response,
                message_type="practice",
                category=subject_str
            )
            return "", history

        # 3. Triage 分类
        classification = triage_agent.classify_sync(message)
        action = classification.get("action", "respond_rejection")

        # 4. 根据意图处理
        if action == "handle_grade_info":
            grade = conversation_manager.extract_grade(message)
            if grade:
                conversation_manager.set_grade(session_id, grade)
            response = f"好的，我已经记录您的年级信息为：{grade or '未指定年级'}。请问有什么数学或历史作业问题需要帮助？"
            history[-1][1] = response
            conversation_manager.add_message(session_id, "user", message, message_type="meta")
            conversation_manager.add_message(session_id, "assistant", response, message_type="meta")

        elif action == "handle_summarize":
            result = answer_generator.generate_summary(session_id)
            summary_text = f"## 对话总结\n\n{result.get('summary', '无法生成总结')}\n\n### 讨论的主题\n"
            summary_text += "、".join(result.get('topics_discussed', [])) or "无"
            history[-1][1] = summary_text
            conversation_manager.add_message(session_id, "user", message, message_type="meta")
            conversation_manager.add_message(session_id, "assistant", summary_text, message_type="summary")

        elif action in ["handoff_to_math", "handoff_to_history"]:
            should_reject, reject_msg = guardrail_agent.check_sync(message)

            if should_reject:
                history[-1][1] = reject_msg
                conversation_manager.add_message(session_id, "user", message, category="invalid")
                conversation_manager.add_message(session_id, "assistant", reject_msg, category="invalid")
            else:
                grade = conversation_manager.get_grade(session_id)
                category = "valid_math" if action == "handoff_to_math" else "valid_history"

                response = answer_generator.generate_answer(
                    question=message,
                    session_id=session_id,
                    category=category,
                    grade=grade,
                    is_followup=is_followup,
                    followup_type=followup_type
                )

                response = _review_and_filter_response(response, message, grade)

                history[-1][1] = response
                conversation_manager.add_message(
                    session_id, "user", message,
                    message_type="question",
                    category=category,
                    is_followup=is_followup
                )
                conversation_manager.add_message(
                    session_id, "assistant", response,
                    message_type="answer",
                    category=category
                )

        elif is_system_request(message):
            response = (
                "我是一个数学和历史作业辅导助手。您可以：\n\n"
                "• 问我数学或历史作业问题\n"
                "• 告诉我您的年级（如'我是大一学生'）\n"
                "• 让我生成练习题（如'给我出几道二次函数的练习题'）\n"
                "• 要求总结对话（如'总结我们的对话'）\n\n"
                "请问有什么可以帮助您的？"
            )
            history[-1][1] = response
            conversation_manager.add_message(session_id, "user", message, message_type="meta")
            conversation_manager.add_message(session_id, "assistant", response, message_type="meta")

        else:
            should_reject, reject_msg = guardrail_agent.check_sync(message)

            if should_reject:
                history[-1][1] = reject_msg
            else:
                history[-1][1] = "抱歉，我无法帮助回答这个问题。我只擅长数学和历史作业问题。"
            conversation_manager.add_message(session_id, "user", message, category="invalid")
            conversation_manager.add_message(session_id, "assistant", history[-1][1], category="invalid")

    except Exception as e:
        history[-1][1] = f"发生错误: {str(e)}"
        print(f"处理消息错误: {e}")

    return "", history


def _review_and_filter_response(
    response: str,
    question: str,
    grade: Optional[str]
) -> str:
    """
    审查并过滤响应

    Args:
        response: 生成的响应
        question: 原始问题
        grade: 用户年级

    Returns:
        处理后的响应
    """
    # 使用输出审查 Agent
    filtered_response, review_result = output_review_agent.review_and_filter(
        response=response,
        original_question=question,
        user_grade=grade
    )

    # 记录审查日志（生产环境可关闭）
    if review_result.issues:
        print(f"[输出审查] 发现 {len(review_result.issues)} 个问题: {review_result.issues}")

    return filtered_response


def _generate_with_streaming(message: str, session_id: str, category: str, grade: str) -> str:
    """
    使用流式输出生成答案

    Args:
        message: 用户问题
        session_id: 会话ID
        category: 问题分类
        grade: 用户年级

    Returns:
        生成的答案
    """
    # 获取对话历史
    history = conversation_manager.get_history(session_id)
    grade_info = grade if grade else "未指定年级"

    # 构建提示
    if category == "valid_math":
        system_prompt = answer_generator._build_math_prompt(grade_info, message)
        task = "math"
    elif category == "valid_history":
        system_prompt = answer_generator._build_history_prompt(grade_info)
        task = "history"
    else:
        system_prompt = ""
        task = "default"

    # 检查是否是追问
    if history and len(history) >= 2:
        context = answer_generator._build_context(history)
        full_question = f"{context}\n\n当前问题: {message}"
    else:
        full_question = message

    # 使用流式调用
    response = multi_model_client.chat_stream(
        message=full_question,
        system_prompt=system_prompt,
        task=task,
        timeout=60
    )

    # 渲染数学公式
    response = render_math(response)

    return response


def _extract_grade(message: str) -> str:
    """从消息中提取年级信息"""
    grade_patterns = {
        "大一": "大一", "大二": "大二", "大三": "大三", "大四": "大四",
        "研一": "研一", "研二": "研二", "研三": "研三",
        "博士": "博士生", "博士生": "博士生",
        "高一": "高一", "高二": "高二", "高三": "高三",
        "初一": "初一", "初二": "初二", "初三": "初三",
        "小学": "小学生"
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


def get_welcome() -> str:
    """获取欢迎语"""
    return WELCOME_MESSAGE


# 创建Gradio界面
with gr.Blocks(
    title="SmartTutor - 作业辅导智能体",
    theme=gr.themes.Soft()
) as demo:
    gr.Markdown("""
    # SmartTutor - 作业辅导智能体

    <div style='text-align: center; color: #666;'>
    帮助您解答数学和历史作业问题 | 支持多轮对话 | 年级适配
    </div>
    """)

    state = gr.State(value={"session_id": None})

    chatbot = gr.Chatbot(
        label="对话历史",
        height=500,
        show_copy_button=True
    )

    with gr.Row():
        msg_input = gr.Textbox(
            label="输入问题",
            placeholder="请输入您的数学或历史作业问题...\n\n示例：\n- x² + 2x + 1 = 0，求 x\n- 法国大革命是什么时候？\n- 给我出几道关于函数的练习题",
            scale=4,
            lines=3
        )

    with gr.Row():
        submit_btn = gr.Button("发送", variant="primary", scale=1)
        clear_btn = gr.Button("清除对话", scale=1)

    gr.Markdown("---")
    gr.Markdown("""
    ### 使用说明

    **功能特性：**
    - ✅ 数学问题：代数、几何、微积分、概率统计等
    - ✅ 历史问题：世界历史、中国历史、历史人物与事件等
    - ✅ 年级适配：告诉我您的年级（如"我是大一学生"），获得更精准的讲解
    - ✅ 练习题生成：输入"给我出几道关于[知识点]的练习题"
    - ✅ 对话总结：输入"总结对话"查看对话摘要

    **使用示例：**
    - 数学: x² + 2x + 1 = 0，求 x
    - 数学: √1000 是有理数吗？
    - 历史: 法国第一任总统是谁？
    - 历史: 香港科技大学第一任校长是谁？（会被礼貌拒绝）
    - 练习: 给我出3道关于二次函数的练习题
    - 总结: 总结我们的对话
    """)

    # 事件绑定
    submit_btn.click(
        fn=process_message,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )

    msg_input.submit(
        fn=process_message,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )

    clear_btn.click(
        fn=clear_history,
        outputs=[msg_input, chatbot]
    )


if __name__ == "__main__":
    # 初始化会话
    init_session()

    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        show_api=False,
        share=False,
        inbrowser=False
    )
