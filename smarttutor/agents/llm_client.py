"""
SmartTutor - 作业辅导智能体
LLM客户端 - 支持多种API提供商
"""

import json
from typing import Optional, Dict, Any, List, Union
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from app.config import ModelConfig


class LLMClient:
    """LLM客户端类 - 支持多种API提供商"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.provider = ModelConfig.get_active_provider()
        self.model_name = ModelConfig.get_model_name()
        self.llm = self._create_llm()
    
    def _create_llm(self):
        """根据配置创建LLM实例"""
        
        # 优先使用配置的 provider
        provider = self.provider
        
        if provider == "deepseek":
            print(f"使用 DeepSeek API: {ModelConfig.DEEPSEEK_MODEL}")
            return self._create_deepseek_llm()
        
        elif provider == "openai":
            print(f"使用 OpenAI API: {ModelConfig.OPENAI_MODEL}")
            return self._create_openai_llm()
        
        elif provider == "hkust_azure":
            print(f"使用 HKUST Azure API: {ModelConfig.HKUST_AZURE_DEPLOYMENT_NAME}")
            return self._create_hkust_azure_llm()
        
        elif provider == "azure":
            print(f"使用 Azure OpenAI API: {ModelConfig.AZURE_OPENAI_DEPLOYMENT_NAME}")
            return self._create_azure_llm()
        
        else:
            print("警告：未配置任何LLM API")
            return None
    
    def _create_deepseek_llm(self):
        """创建DeepSeek LLM实例（使用 OpenAI 兼容接口）"""
        return ChatOpenAI(
            model=ModelConfig.DEEPSEEK_MODEL,
            api_key=ModelConfig.DEEPSEEK_API_KEY,
            base_url=ModelConfig.DEEPSEEK_BASE_URL,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def _create_openai_llm(self):
        """创建标准OpenAI LLM实例"""
        return ChatOpenAI(
            model=ModelConfig.OPENAI_MODEL,
            api_key=ModelConfig.OPENAI_API_KEY,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def _create_hkust_azure_llm(self):
        """创建HKUST Azure API LLM实例"""
        return AzureChatOpenAI(
            azure_deployment=ModelConfig.HKUST_AZURE_DEPLOYMENT_NAME,
            azure_endpoint=ModelConfig.HKUST_AZURE_ENDPOINT,
            api_key=ModelConfig.HKUST_AZURE_API_KEY,
            api_version=ModelConfig.HKUST_AZURE_API_VERSION,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def _create_azure_llm(self):
        """创建标准Azure OpenAI LLM实例"""
        return AzureChatOpenAI(
            azure_deployment=ModelConfig.AZURE_OPENAI_DEPLOYMENT_NAME,
            azure_endpoint=ModelConfig.AZURE_OPENAI_ENDPOINT,
            api_key=ModelConfig.AZURE_OPENAI_API_KEY,
            api_version=ModelConfig.AZURE_OPENAI_API_VERSION,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """发送聊天请求"""
        if self.llm is None:
            return "错误：LLM未配置。请在.env文件中配置API密钥。"
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            error_msg = str(e)
            print(f"LLM调用错误: {error_msg}")
            return f"发生错误: {error_msg}"
    
    def chat_with_history(self, messages: list, system_prompt: Optional[str] = None) -> str:
        """发送带历史的聊天请求"""
        if self.llm is None:
            return "错误：LLM未配置。请在.env文件中配置API密钥。"
        
        chat_messages = []
        if system_prompt:
            chat_messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        for msg in messages:
            if msg["role"] == "user":
                chat_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_messages.append(SystemMessage(content=msg["content"]))
        
        try:
            response = self.llm.invoke(chat_messages)
            return response.content
        except Exception as e:
            error_msg = str(e)
            print(f"LLM调用错误: {error_msg}")
            return f"发生错误: {error_msg}"
    
    def structured_output(self, message: str, system_prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """获取结构化输出"""
        response = self.chat(message, system_prompt)
        
        if format_json:
            try:
                # 尝试解析JSON
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
    
    def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        if self.llm is None:
            return {"success": False, "message": "LLM未配置"}
        
        try:
            test_message = "Hello, please respond with 'OK' if you receive this."
            response = self.llm.invoke([HumanMessage(content=test_message)])
            return {
                "success": True,
                "message": "连接成功",
                "provider": self.provider,
                "model": self.model_name,
                "response": response.content[:100]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
                "provider": self.provider,
                "model": self.model_name
            }
    
    def list_models(self) -> Dict[str, Any]:
        """查询可用的模型列表"""
        import requests
        
        if not ModelConfig.is_hkust_azure_configured():
            return {"success": False, "message": "HKUST Azure 未配置"}
        
        endpoints = [
            f"{ModelConfig.HKUST_AZURE_ENDPOINT}/openai/models",
            f"{ModelConfig.HKUST_AZURE_ENDPOINT}/v1/models",
            f"{ModelConfig.HKUST_AZURE_ENDPOINT}/models",
        ]
        
        for url in endpoints:
            try:
                headers = {
                    "api-key": ModelConfig.HKUST_AZURE_API_KEY,
                    "Content-Type": "application/json"
                }
                if "openai" in url:
                    url += f"?api-version={ModelConfig.HKUST_AZURE_API_VERSION}"
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "message": f"获取成功 (端点: {url})",
                        "models": data,
                        "endpoint": url
                    }
            except Exception as e:
                continue
        
        return {
            "success": False,
            "message": "无法获取模型列表，请联系老师获取可用的deployment名称",
            "provider": self.provider
        }


# 全局LLM客户端实例
llm_client = LLMClient()
