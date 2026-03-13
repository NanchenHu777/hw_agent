"""
SmartTutor - 作业辅导智能体
使用 OpenAI Agents SDK 的专家 Agent
"""

import sys
import os

# 添加 SDK 路径
sdk_path = os.path.join(os.path.dirname(__file__), "sdk")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

from typing import Optional, Dict, Any
from agents import Agent
from pydantic import BaseModel

# 导入模型工厂
from agents.model_factory import (
    get_model_for_task,
    build_deepseek_model,
    build_hkust_azure_model,
    build_azure_model,
    build_openai_model,
)
from app.config import ModelConfig


# ==================== 数学导师 Agent ====================

def create_math_tutor_agent() -> Agent:
    """
    创建数学导师 Agent
    使用 DeepSeek 模型（性价比高，数学能力强）
    """
    try:
        model = get_model_for_task("math")
    except Exception as e:
        print(f"创建数学导师失败: {e}")
        # 回退到默认模型
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


# ==================== 历史导师 Agent ====================

def create_history_tutor_agent() -> Agent:
    """
    创建历史导师 Agent
    使用 Azure 模型（适合历史/哲学问题）
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


# ==================== 全局 Agent 实例 ====================

# 延迟创建 Agent，确保模型配置已加载
_math_tutor_agent: Optional[Agent] = None
_history_tutor_agent: Optional[Agent] = None


def get_math_tutor() -> Agent:
    """获取数学导师 Agent（延迟初始化）"""
    global _math_tutor_agent
    if _math_tutor_agent is None:
        _math_tutor_agent = create_math_tutor_agent()
    return _math_tutor_agent


def get_history_tutor() -> Agent:
    """获取历史导师 Agent（延迟初始化）"""
    global _history_tutor_agent
    if _history_tutor_agent is None:
        _history_tutor_agent = create_history_tutor_agent()
    return _history_tutor_agent
