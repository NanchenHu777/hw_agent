"""
SmartTutor - 作业辅导智能体
多模型客户端 - 支持根据任务类型选择不同模型、流式输出、超时处理
"""

import json
import time
from typing import Optional, Dict, Any, List, Iterator, Callable
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from app.config import ModelConfig


class TimeoutException(Exception):
    """超时异常"""
    pass


class MultiModelClient:
    """
    多模型客户端
    根据任务类型自动选择合适的模型
    - 数学问题：使用配置的 MATH_MODEL（推荐 o1-mini）
    - 历史问题：使用配置的 HISTORY_MODEL（推荐 gpt-4o）
    - 其他任务：使用 DEFAULT_MODEL

    支持功能：
    - 普通调用
    - 流式输出
    - 超时控制
    """

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 60

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
            max_tokens=ModelConfig.MODEL_MAX_TOKENS,
            request_timeout=self.DEFAULT_TIMEOUT
        )

    def _create_deepseek_llm(self):
        """创建 DeepSeek LLM"""
        return ChatOpenAI(
            model=ModelConfig.DEEPSEEK_MODEL,
            api_key=ModelConfig.DEEPSEEK_API_KEY,
            base_url=ModelConfig.DEEPSEEK_BASE_URL,
            temperature=ModelConfig.MODEL_TEMPERATURE,
            max_tokens=ModelConfig.MODEL_MAX_TOKENS,
            request_timeout=self.DEFAULT_TIMEOUT
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
            error_msg = str(e)
            print(f"LLM调用错误 ({task}): {error_msg}")

            # 处理超时
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                return "抱歉，模型响应时间过长，请稍后重试。"

            # 处理其他错误
            return f"发生错误: {error_msg}"

    def chat_stream(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        task: str = "default",
        timeout: int = DEFAULT_TIMEOUT,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        流式发送聊天请求

        Args:
            message: 用户消息
            system_prompt: 系统提示
            task: 任务类型
            timeout: 超时时间（秒）
            progress_callback: 进度回调函数

        Returns:
            完整的响应文本
        """
        llm = self.get_llm(task)

        if llm is None:
            return "错误：LLM未配置。请在.env文件中配置API密钥。"

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))

        full_response = []
        start_time = time.time()

        try:
            # 使用流式调用
            for chunk in llm.stream(messages):
                # 检查超时
                if time.time() - start_time > timeout:
                    # 如果已经有一些响应，返回部分结果
                    if full_response:
                        partial = "".join(full_response)
                        return partial + "\n\n[响应超时，以下是已生成的部分内容...]"
                    raise TimeoutException("模型响应超时")

                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response.append(content)
                    if progress_callback:
                        progress_callback(content)

            return "".join(full_response)

        except TimeoutException:
            return "抱歉，模型响应时间过长，请稍后重试。"
        except Exception as e:
            error_msg = str(e)
            print(f"LLM流式调用错误 ({task}): {error_msg}")

            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                return "抱歉，模型响应时间过长，请稍后重试。"

            return f"发生错误: {error_msg}"

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

    def chat_with_history_stream(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        task: str = "default",
        timeout: int = DEFAULT_TIMEOUT
    ) -> Iterator[str]:
        """
        流式发送带历史的聊天请求

        Args:
            messages: 消息历史列表
            system_prompt: 系统提示
            task: 任务类型
            timeout: 超时时间

        Yields:
            响应文本块
        """
        llm = self.get_llm(task)

        if llm is None:
            yield "错误：LLM未配置。请在.env文件中配置API密钥。"
            return

        chat_messages = []
        if system_prompt:
            chat_messages.append(SystemMessage(content=system_prompt))

        for msg in messages:
            if msg["role"] == "user":
                chat_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_messages.append(AIMessage(content=msg["content"]))

        start_time = time.time()

        try:
            for chunk in llm.stream(chat_messages):
                # 检查超时
                if time.time() - start_time > timeout:
                    yield "\n\n[响应超时]"
                    return

                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    yield content

        except Exception as e:
            error_msg = str(e)
            print(f"LLM流式调用错误 ({task}): {error_msg}")

            if "timeout" in error_msg.lower():
                yield "抱歉，模型响应时间过长，请稍后重试。"
            else:
                yield f"发生错误: {error_msg}"

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
