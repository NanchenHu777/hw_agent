"""
SmartTutor - 作业辅导智能体
多模型客户端 - 支持根据任务类型选择不同模型
"""

import json
from typing import Optional, Dict, Any, List
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from app.config import ModelConfig


class MultiModelClient:
    """
    多模型客户端
    根据任务类型自动选择合适的模型
    - 数学问题：使用配置的 MATH_MODEL（推荐 o1-mini）
    - 历史问题：使用配置的 HISTORY_MODEL（推荐 gpt-4o）
    - 其他任务：使用 DEFAULT_MODEL
    """
    
    def __init__(self):
        """初始化多模型客户端"""
        self._llms: Dict[str, Any] = {}
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保模型已初始化"""
        if not self._initialized:
            self._init_llms()
            self._initialized = True
    
    def _init_llms(self):
        """初始化所有需要的模型"""
        if ModelConfig.is_hkust_azure_configured():
            # 数学模型
            self._llms["math"] = self._create_azure_llm(ModelConfig.MATH_MODEL)
            # 历史模型
            self._llms["history"] = self._create_azure_llm(ModelConfig.HISTORY_MODEL)
            # 默认模型（用于 triage、guardrail）
            self._llms["default"] = self._create_azure_llm(ModelConfig.DEFAULT_MODEL)
            # 兼容旧接口
            self._llms["triage"] = self._llms["default"]
            self._llms["guardrail"] = self._llms["default"]
        
        # 如果配置了 DeepSeek，也添加
        if ModelConfig.is_deepseek_configured():
            self._llms["deepseek"] = self._create_deepseek_llm()
    
    def _create_azure_llm(self, deployment_name: str):
        """创建 Azure LLM"""
        return AzureChatOpenAI(
            azure_deployment=deployment_name,
            azure_endpoint=ModelConfig.HKUST_AZURE_ENDPOINT,
            api_key=ModelConfig.HKUST_AZURE_API_KEY,
            api_version=ModelConfig.HKUST_AZURE_API_VERSION,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def _create_deepseek_llm(self):
        """创建 DeepSeek LLM"""
        return ChatOpenAI(
            model=ModelConfig.DEEPSEEK_MODEL,
            api_key=ModelConfig.DEEPSEEK_API_KEY,
            base_url=ModelConfig.DEEPSEEK_BASE_URL,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def get_llm(self, task: str = "default"):
        """获取指定任务的 LLM"""
        self._ensure_initialized()
        
        if task in self._llms:
            return self._llms[task]
        return self._llms.get("default")
    
    def chat(self, message: str, system_prompt: Optional[str] = None, task: str = "default") -> str:
        """发送聊天请求"""
        llm = self.get_llm(task)
        
        if llm is None:
            return "错误：LLM未配置。请在.env文件中配置API密钥。"
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))
        
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"LLM调用错误 ({task}): {e}")
            return f"发生错误: {str(e)}"
    
    def chat_with_history(self, messages: list, system_prompt: Optional[str] = None, task: str = "default") -> str:
        """发送带历史的聊天请求"""
        llm = self.get_llm(task)
        
        if llm is None:
            return "错误：LLM未配置。请在.env文件中配置API密钥。"
        
        chat_messages = []
        if system_prompt:
            chat_messages.append(SystemMessage(content=system_prompt))
        
        for msg in messages:
            if msg["role"] == "user":
                chat_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_messages.append(SystemMessage(content=msg["content"]))
        
        try:
            response = llm.invoke(chat_messages)
            return response.content
        except Exception as e:
            print(f"LLM调用错误 ({task}): {e}")
            return f"发生错误: {str(e)}"
    
    def structured_output(self, message: str, system_prompt: str, task: str = "default", format_json: bool = True) -> Dict[str, Any]:
        """获取结构化输出"""
        response = self.chat(message, system_prompt, task)
        
        if format_json:
            try:
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                elif response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                return json.loads(response.strip())
            except json.JSONDecodeError as e:
                return {"error": f"无法解析JSON: {e}", "raw": response}
        
        return {"response": response}


# 全局多模型客户端实例
multi_model_client = MultiModelClient()
