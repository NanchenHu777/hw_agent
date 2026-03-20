"""
Multi-model client for SmartTutor.
"""

import json
from typing import Any, Dict, Optional

from langchain_openai import AzureChatOpenAI, ChatOpenAI

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:  # pragma: no cover - compatibility with older langchain
    from langchain.schema import HumanMessage, SystemMessage

from app.config import ModelConfig


class MultiModelClient:
    """Route tasks to the configured model and fall back when needed."""

    def __init__(self):
        self._llms: Dict[str, Any] = {}
        self._initialized = False

    def _ensure_initialized(self):
        if not self._initialized:
            self._init_llms()
            self._initialized = True

    def _init_llms(self):
        if ModelConfig.is_hkust_azure_configured():
            self._llms["math"] = self._create_azure_llm(ModelConfig.MATH_MODEL)
            self._llms["history"] = self._create_azure_llm(ModelConfig.HISTORY_MODEL)
            self._llms["default"] = self._create_azure_llm(ModelConfig.DEFAULT_MODEL)
            self._llms["triage"] = self._llms["default"]
            self._llms["guardrail"] = self._llms["default"]

        if ModelConfig.is_deepseek_configured():
            self._llms["deepseek"] = self._create_deepseek_llm()

    def _create_azure_llm(self, deployment_name: str):
        return AzureChatOpenAI(
            azure_deployment=deployment_name,
            azure_endpoint=ModelConfig.HKUST_AZURE_ENDPOINT,
            api_key=ModelConfig.HKUST_AZURE_API_KEY,
            api_version=ModelConfig.HKUST_AZURE_API_VERSION,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS,
        )

    def _create_deepseek_llm(self):
        return ChatOpenAI(
            model=ModelConfig.DEEPSEEK_MODEL,
            api_key=ModelConfig.DEEPSEEK_API_KEY,
            base_url=ModelConfig.DEEPSEEK_BASE_URL,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS,
        )

    def get_llm(self, task: str = "default"):
        self._ensure_initialized()
        if task in self._llms:
            return self._llms[task]
        return self._llms.get("default")

    def _should_fallback_to_default(self, task: str, error: Exception) -> bool:
        if task == "default":
            return False

        error_text = str(error).lower()
        markers = [
            "team_model_access_denied",
            "not allowed to access model",
            "access_denied",
            "401",
        ]
        return any(marker in error_text for marker in markers)

    def _invoke_with_fallback(self, llm, messages, task: str) -> str:
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as error:
            if self._should_fallback_to_default(task, error):
                fallback_llm = self.get_llm("default")
                if fallback_llm is not None and fallback_llm is not llm:
                    try:
                        print(f"LLM调用回退: {task} -> default")
                        response = fallback_llm.invoke(messages)
                        return response.content
                    except Exception as fallback_error:
                        print(f"LLM回退失败 ({task} -> default): {fallback_error}")

            print(f"LLM调用错误 ({task}): {error}")
            return f"发生错误: {error}"

    def chat(self, message: str, system_prompt: Optional[str] = None, task: str = "default") -> str:
        llm = self.get_llm(task)
        if llm is None:
            return "错误：LLM未配置。请在 .env 文件中配置 API 密钥。"

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))

        return self._invoke_with_fallback(llm, messages, task)

    def chat_with_history(self, messages: list, system_prompt: Optional[str] = None, task: str = "default") -> str:
        llm = self.get_llm(task)
        if llm is None:
            return "错误：LLM未配置。请在 .env 文件中配置 API 密钥。"

        chat_messages = []
        if system_prompt:
            chat_messages.append(SystemMessage(content=system_prompt))

        for msg in messages:
            if msg["role"] == "user":
                chat_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_messages.append(SystemMessage(content=msg["content"]))

        return self._invoke_with_fallback(llm, chat_messages, task)

    def structured_output(
        self,
        message: str,
        system_prompt: str,
        task: str = "default",
        format_json: bool = True,
    ) -> Dict[str, Any]:
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
            except json.JSONDecodeError as error:
                return {"error": f"无法解析JSON: {error}", "raw": response}

        return {"response": response}


multi_model_client = MultiModelClient()
