"""
Legacy LLM client for SmartTutor.
Supports multiple API providers.
"""

import json
from typing import Optional, Dict, Any, List, Union

from langchain_openai import AzureChatOpenAI, ChatOpenAI

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:  # pragma: no cover - compatibility with older langchain
    from langchain.schema import HumanMessage, SystemMessage
from app.config import ModelConfig


class LLMClient:
    """Legacy LLM client that supports multiple providers."""
    
    def __init__(self):
        """Initialize the legacy LLM client."""
        self.provider = ModelConfig.get_active_provider()
        self.model_name = ModelConfig.get_model_name()
        self.llm = self._create_llm()
    
    def _create_llm(self):
        """Create the configured LLM instance."""
        
        # Prefer the provider explicitly selected in configuration.
        provider = self.provider
        
        if provider == "deepseek":
            print(f"Using DeepSeek API: {ModelConfig.DEEPSEEK_MODEL}")
            return self._create_deepseek_llm()
        
        elif provider == "openai":
            print(f"Using OpenAI API: {ModelConfig.OPENAI_MODEL}")
            return self._create_openai_llm()
        
        elif provider == "hkust_azure":
            print(f"Using HKUST Azure API: {ModelConfig.HKUST_AZURE_DEPLOYMENT_NAME}")
            return self._create_hkust_azure_llm()
        
        elif provider == "azure":
            print(f"Using Azure OpenAI API: {ModelConfig.AZURE_OPENAI_DEPLOYMENT_NAME}")
            return self._create_azure_llm()
        
        else:
            print("Warning: no LLM API is configured.")
            return None
    
    def _create_deepseek_llm(self):
        """Create a DeepSeek client through the OpenAI-compatible API."""
        return ChatOpenAI(
            model=ModelConfig.DEEPSEEK_MODEL,
            api_key=ModelConfig.DEEPSEEK_API_KEY,
            base_url=ModelConfig.DEEPSEEK_BASE_URL,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def _create_openai_llm(self):
        """Create a standard OpenAI chat client."""
        return ChatOpenAI(
            model=ModelConfig.OPENAI_MODEL,
            api_key=ModelConfig.OPENAI_API_KEY,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def _create_hkust_azure_llm(self):
        """Create an HKUST Azure chat client."""
        return AzureChatOpenAI(
            azure_deployment=ModelConfig.HKUST_AZURE_DEPLOYMENT_NAME,
            azure_endpoint=ModelConfig.HKUST_AZURE_ENDPOINT,
            api_key=ModelConfig.HKUST_AZURE_API_KEY,
            api_version=ModelConfig.HKUST_AZURE_API_VERSION,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def _create_azure_llm(self):
        """Create a standard Azure OpenAI chat client."""
        return AzureChatOpenAI(
            azure_deployment=ModelConfig.AZURE_OPENAI_DEPLOYMENT_NAME,
            azure_endpoint=ModelConfig.AZURE_OPENAI_ENDPOINT,
            api_key=ModelConfig.AZURE_OPENAI_API_KEY,
            api_version=ModelConfig.AZURE_OPENAI_API_VERSION,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS
        )
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """Send a single-turn chat request."""
        if self.llm is None:
            return "Error: no LLM is configured. Please add API credentials to the .env file."
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            error_msg = str(e)
            print(f"LLM error: {error_msg}")
            return f"Error: {error_msg}"
    
    def chat_with_history(self, messages: list, system_prompt: Optional[str] = None) -> str:
        """Send a chat request with prior message history."""
        if self.llm is None:
            return "Error: no LLM is configured. Please add API credentials to the .env file."
        
        chat_messages = []
        if system_prompt:
            chat_messages.append(SystemMessage(content=system_prompt))
        
        # Replay the stored message history into the prompt.
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
            print(f"LLM error: {error_msg}")
            return f"Error: {error_msg}"
    
    def structured_output(self, message: str, system_prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Return structured JSON output when the model provides it."""
        response = self.chat(message, system_prompt)
        
        if format_json:
            try:
                # Strip optional Markdown fences before parsing JSON.
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                elif response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                return json.loads(response.strip())
            except json.JSONDecodeError as e:
                return {"error": f"Unable to parse JSON: {e}", "raw": response}
        
        return {"response": response}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test whether the configured API can answer a simple request."""
        if self.llm is None:
            return {"success": False, "message": "No LLM is configured."}
        
        try:
            test_message = "Hello, please respond with 'OK' if you receive this."
            response = self.llm.invoke([HumanMessage(content=test_message)])
            return {
                "success": True,
                "message": "Connection successful.",
                "provider": self.provider,
                "model": self.model_name,
                "response": response.content[:100]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "provider": self.provider,
                "model": self.model_name
            }
    
    def list_models(self) -> Dict[str, Any]:
        """Attempt to list available models from the HKUST Azure endpoint."""
        import requests
        
        if not ModelConfig.is_hkust_azure_configured():
            return {"success": False, "message": "HKUST Azure is not configured."}
        
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
                        "message": f"Successfully fetched models from {url}",
                        "models": data,
                        "endpoint": url
                    }
            except Exception as e:
                continue
        
        return {
            "success": False,
            "message": "Unable to fetch the model list. Please confirm the available deployment names.",
            "provider": self.provider
        }


# Global legacy client instance.
llm_client = LLMClient()
