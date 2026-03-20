"""
Legacy model factory for OpenAI Agents SDK integrations.
"""

import re
import sys
import os

# Add the bundled SDK path when present.
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
    Create an HKUST Azure model client for the Agents SDK.
    """
    if not ModelConfig.HKUST_AZURE_API_KEY:
        raise RuntimeError("HKUST Azure API 未配置")
    
    endpoint = ModelConfig.HKUST_AZURE_ENDPOINT
    deployment = ModelConfig.HKUST_AZURE_DEPLOYMENT_NAME
    api_version = ModelConfig.HKUST_AZURE_API_VERSION
    
    # Extract the Azure base URL from the configured endpoint.
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
    Create a standard Azure OpenAI model client.
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
    Create a DeepSeek model client.
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
    Create a standard OpenAI model client.
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
    Return the preferred model for a given task.
    
    Args:
        task: Task type ("math", "history", "triage", "guardrail").
        
    Returns:
        Configured ``OpenAIChatCompletionsModel`` instance.
    """
    # Prefer DeepSeek for math when it is available.
    if task == "math":
        if ModelConfig.is_deepseek_configured():
            print(f"使用 DeepSeek 模型处理数学问题: {ModelConfig.DEEPSEEK_MODEL}")
            return build_deepseek_model()
        else:
            print("警告: DeepSeek 未配置，回退到 HKUST Azure")
    
    # Prefer Azure-based models for history and routing tasks.
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
    
    # Fall back to the HKUST Azure deployment when possible.
    if ModelConfig.is_hkust_azure_configured():
        return build_hkust_azure_model()
    
    raise RuntimeError("没有任何模型配置可用")
