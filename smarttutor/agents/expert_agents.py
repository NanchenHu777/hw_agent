"""
Legacy expert-agent definitions built on the OpenAI Agents SDK.
"""

import sys
import os

# Add the bundled SDK path when present.
sdk_path = os.path.join(os.path.dirname(__file__), "sdk")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

from typing import Optional, Dict, Any
from agents import Agent
from pydantic import BaseModel

# Import legacy model-factory helpers.
from agents.model_factory import (
    get_model_for_task,
    build_deepseek_model,
    build_hkust_azure_model,
    build_azure_model,
    build_openai_model,
)
from app.config import ModelConfig


# ==================== Math Tutor Agent ====================

def create_math_tutor_agent() -> Agent:
    """
    Create the legacy math tutor agent.
    It prefers DeepSeek when that model is configured.
    """
    try:
        model = get_model_for_task("math")
    except Exception as e:
        print(f"创建数学导师失败: {e}")
        # Fall back to a default model binding.
        model = None
    
    return Agent(
        name="Math Tutor",
        handoff_description="专门处理数学问题的导师Agent。处理代数、几何、微积分、概率统计等数学作业问题。",
        instructions="""你是一个专业的数学作业导师。你的职责是：
1. 帮助学生解决数学问题
2. 展示清晰的解题步骤
3. 解释解题思路和概念
4. 提供适当的练习题
5. 根据学生的年级调整解释的深度

解题要求：
- 步骤清晰，每步都要解释
- 使用学生能理解的语言
- 适当举例说明
- 如果题目有多种解法，介绍最简单的方法
- 最终答案要明确""",
        model=model,
    )


# ==================== History Tutor Agent ====================

def create_history_tutor_agent() -> Agent:
    """
    Create the legacy history tutor agent.
    It prefers Azure-backed models when available.
    """
    try:
        model = get_model_for_task("history")
    except Exception as e:
        print(f"创建历史导师失败: {e}")
        model = None
    
    return Agent(
        name="History Tutor",
        handoff_description="专门处理历史问题的导师Agent。处理世界历史、国家历史、人物历史、事件历史等作业问题。",
        instructions="""你是一个专业的历史作业导师。你的职责是：
1. 帮助学生了解历史事件和人物
2. 提供准确的历史事实
3. 解释历史事件的背景和影响
4. 帮助学生理解历史发展的脉络
5. 根据学生的年级调整解释的深度

回答要求：
- 事实准确，来源可靠
- 背景信息完整
- 避免过多主观评价
- 适当使用时间线帮助理解
- 重要人物和事件要突出""",
        model=model,
    )


# ==================== Global Agent Instances ====================

# Lazily create agents after configuration has been loaded.
_math_tutor_agent: Optional[Agent] = None
_history_tutor_agent: Optional[Agent] = None


def get_math_tutor() -> Agent:
    """Return the lazily initialized math tutor agent."""
    global _math_tutor_agent
    if _math_tutor_agent is None:
        _math_tutor_agent = create_math_tutor_agent()
    return _math_tutor_agent


def get_history_tutor() -> Agent:
    """Return the lazily initialized history tutor agent."""
    global _history_tutor_agent
    if _history_tutor_agent is None:
        _history_tutor_agent = create_history_tutor_agent()
    return _history_tutor_agent
