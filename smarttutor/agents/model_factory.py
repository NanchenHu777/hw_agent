"""
SmartTutor - 作业辅导智能体
OpenAI Agents SDK 模型工厂
支持创建 Agents SDK 兼容的模型实例
"""

import re
import sys
import os

# 添加 SDK 路径
sdk_path = os.path.join(os.path.dirname(__file__), "sdk")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

from typing import Optional
from agents.sdk.openai import AsyncOpenAI
from agents.sdk.openai import AzureOpenAI as AsyncAzureOpenAI
from agents import OpenAIChatCompletionsModel
from app.config import ModelConfig


def build_hkust_azure_model() -> OpenAIChatCompletionsModel:
    """
    创建 HKUST Azure API 模型（用于历史/哲学问题）
    """
    if not ModelConfig.HKUST_AZURE_API_KEY:
        raise RuntimeError("HKUST Azure API 未配置")
    
    endpoint = ModelConfig.HKUST_AZURE_ENDPOINT
    deployment = ModelConfig.HKUST_AZURE_DEPLOYMENT_NAME
    api_version = ModelConfig.HKUST_AZURE_API_VERSION
    
    # 解析 endpoint 提取基础 URL
    match = re.match(
        r"(https?://[^/]+)(/.*)?",
        endpoint,
    )
    if match:
        azure_endpoint = match.group(1)
    else:
        azure_endpoint = endpoint
    
    client = AsyncAzureOpenAI(
        api_key=ModelConfig.HKUST_AZURE_API_KEY,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
    )
    
    return OpenAIChatCompletionsModel(
        openai_client=client,
        model=deployment,
    )


def build_azure_model() -> OpenAIChatCompletionsModel:
    """
    创建标准 Azure OpenAI 模型
    """
    if not ModelConfig.AZURE_OPENAI_ENDPOINT or not ModelConfig.AZURE_OPENAI_API_KEY:
        raise RuntimeError("Azure OpenAI 未配置")
    
    endpoint = ModelConfig.AZURE_OPENAI_ENDPOINT
    deployment = ModelConfig.AZURE_OPENAI_DEPLOYMENT_NAME
    api_version = ModelConfig.AZURE_OPENAI_API_VERSION
    
    match = re.match(
        r"(https?://[^/]+)/openai/deployments/([^/]+)/.*api-version=([^&]+)",
        endpoint,
    )
    if match:
        azure_endpoint = match.group(1)
        deployment = match.group(2)
        api_version = match.group(3)
    
    client = AsyncAzureOpenAI(
        api_key=ModelConfig.AZURE_OPENAI_API_KEY,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
    )
    
    return OpenAIChatCompletionsModel(
        openai_client=client,
        model=deployment,
    )


def build_deepseek_model() -> OpenAIChatCompletionsModel:
    """
    创建 DeepSeek 模型（用于数学问题）
    """
    if not ModelConfig.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek API 未配置")
    
    client = AsyncOpenAI(
        api_key=ModelConfig.DEEPSEEK_API_KEY,
        base_url=ModelConfig.DEEPSEEK_BASE_URL,
    )
    
    return OpenAIChatCompletionsModel(
        openai_client=client,
        model=ModelConfig.DEEPSEEK_MODEL,
    )


def build_openai_model() -> OpenAIChatCompletionsModel:
    """
    创建标准 OpenAI 模型
    """
    if not ModelConfig.OPENAI_API_KEY:
        raise RuntimeError("OpenAI API 未配置")
    
    client = AsyncOpenAI(
        api_key=ModelConfig.OPENAI_API_KEY,
    )
    
    return OpenAIChatCompletionsModel(
        openai_client=client,
        model=ModelConfig.OPENAI_MODEL,
    )


def get_model_for_task(task: str) -> OpenAIChatCompletionsModel:
    """
    根据任务类型获取合适的模型
    
    Args:
        task: 任务类型 ("math", "history", "triage", "guardrail")
        
    Returns:
        OpenAIChatCompletionsModel 实例
    """
    # 数学问题使用 DeepSeek（便宜且效果好）
    if task == "math":
        if ModelConfig.is_deepseek_configured():
            print(f"使用 DeepSeek 模型处理数学问题: {ModelConfig.DEEPSEEK_MODEL}")
            return build_deepseek_model()
        else:
            print("警告: DeepSeek 未配置，回退到 HKUST Azure")
    
    # 历史/其他问题使用 Azure
    if task in ("history", "triage", "guardrail"):
        if ModelConfig.is_hkust_azure_configured():
            print(f"使用 HKUST Azure 模型处理 {task}: {ModelConfig.HKUST_AZURE_DEPLOYMENT_NAME}")
            return build_hkust_azure_model()
        elif ModelConfig.is_azure_configured():
            print(f"使用 Azure 模型处理 {task}: {ModelConfig.AZURE_OPENAI_DEPLOYMENT_NAME}")
            return build_azure_model()
        elif ModelConfig.is_openai_configured():
            print(f"使用 OpenAI 模型处理 {task}: {ModelConfig.OPENAI_MODEL}")
            return build_openai_model()
    
    # 默认返回 HKUST Azure
    if ModelConfig.is_hkust_azure_configured():
        return build_hkust_azure_model()
    
    raise RuntimeError("没有任何模型配置可用")
