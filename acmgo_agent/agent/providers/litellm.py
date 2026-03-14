"""
LiteLLM Provider implementation.

Uses litellm.completion() to support 100+ LLM providers and models.
https://docs.litellm.ai/
"""
import json
import os
import time
import threading
from typing import List, Dict, Any, Optional
from .base import LLMProvider, Message, ToolCall, ToolDefinition


class RateLimiter:
    """简单的速率限制器，确保两次请求之间有最小时间间隔。"""

    def __init__(self, min_interval: float = 0.05):
        """
        初始化速率限制器。

        Args:
            min_interval: 请求之间的最小时间间隔（秒）。
                       0.05 秒 = 每秒 20 个请求。
        """
        self.min_interval = min_interval
        self.last_call_time = 0
        self.lock = threading.Lock()

    def acquire(self):
        """如需等待以符合速率限制。"""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_call_time
            if time_since_last < self.min_interval:
                time.sleep(self.min_interval - time_since_last)
            self.last_call_time = time.time()


def _parse_tool_arguments(arguments: Any) -> Dict[str, Any]:
    """
    从各种格式解析工具参数。

    部分提供商（如 zai/glm）返回 JSON 字符串格式，
    而其他提供商返回字典格式。

    Args:
        arguments: 工具调用的参数（字典或字符串）。

    Returns:
        解析后的参数字典。
    """
    if isinstance(arguments, dict):
        return arguments
    elif isinstance(arguments, str):
        try:
            return json.loads(arguments)
        except json.JSONDecodeError:
            return {}
    return {}


class LiteLLMProvider(LLMProvider):
    """
    LiteLLM 统一 LLM 提供商。

    支持 100+ 提供商，包括：
    - Anthropic: anthropic/claude-opus-4-6
    - OpenAI: openai/gpt-4o
    - Google: google/gemini-pro
    - Cohere: cohere/command-r
    - 以及更多...

    详见 https://docs.litellm.ai/ 查看完整支持的模型列表。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "anthropic/claude-opus-4-6",
        rate_limit_min_interval: float = 0.05,
        **kwargs
    ):
        """
        初始化 LiteLLM 提供商。

        Args:
            api_key: API 密钥。如果为 None，则根据模型前缀从环境变量读取。
                例如，anthropic/ 模型使用 ANTHROPIC_API_KEY。
                也可以使用 LITELLM_API_KEY 作为备选。
            model: litellm 格式的模型名称（例如 "anthropic/claude-opus-4-6"）。
            rate_limit_min_interval: 请求之间的最小时间间隔（秒）（默认：0.05 = 20 次/秒）。
            **kwargs: 额外的 litellm 参数（drop_params 等）。
        """
        try:
            import litellm
        except ImportError:
            raise ImportError(
                "LiteLLM 提供商需要 'litellm' 包。"
                "请安装：uv pip install litellm"
            )

        # LiteLLM 根据模型前缀自动处理来自环境变量的 API 密钥
        # （例如，anthropic/ 模型使用 ANTHROPIC_API_KEY）
        if api_key:
            # Set the API key for the specific provider
            self._set_api_key_for_model(model, api_key)

        super().__init__(model)
        self.litellm = litellm
        self.litellm_params = kwargs
        # Rate limiter: use configured interval
        self.rate_limiter = RateLimiter(min_interval=rate_limit_min_interval)

    def _set_api_key_for_model(self, model: str, api_key: str):
        """为模型的提供商设置 API 密钥。"""
        import litellm

        # 从模型名称中提取提供商（例如 "anthropic/claude-opus-4-6" -> "anthropic"）
        provider = model.split("/")[0].lower()

        # 将提供商名称映射到 litellm 期望的环境变量名
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "cohere": "COHERE_API_KEY",
            "zai": "ZAI_API_KEY",
            "azure": "AZURE_API_KEY",
            "replicate": "REPLICATE_API_TOKEN",
            "huggingface": "HUGGING_FACE_API_KEY",
            "together": "TOGETHERAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "bedrock": "AWS_ACCESS_KEY_ID",
        }

        # 为提供商设置环境变量
        if provider in env_var_map:
            os.environ[env_var_map[provider]] = api_key
        else:
            # 回退到通用 litellm API 密钥
            os.environ["LITELLM_API_KEY"] = api_key

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用 litellm.completion() 发送聊天完成请求。

        Args:
            messages: Message 对象列表。
            tools: 可选的 ToolDefinition 对象列表。
            **kwargs: 额外参数（max_tokens、temperature 等）。

        Returns:
            包含 'content' 和可选的 'tool_calls' 的字典。
        """
        # 转换消息为 litellm 格式
        litellm_messages = self._convert_messages(messages)

        # 转换工具为 litellm 格式
        litellm_tools = None
        if tools:
            litellm_tools = self._convert_tools(tools)

        # 设置参数
        params = {
            "model": self.model,
            "messages": litellm_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        if litellm_tools:
            params["tools"] = litellm_tools

        # 添加可选参数
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]

        # 添加初始化时的 litellm 特定参数
        params.update(self.litellm_params)

        # 应用速率限制（使用 .env 中的配置间隔）
        self.rate_limiter.acquire()

        # 发起 API 调用
        response = self.litellm.completion(**params)

        # 解析响应
        result = {"content": "", "tool_calls": []}

        # 处理不同的响应格式
        if hasattr(response, "choices"):
            # OpenAI 风格的响应
            choice = response.choices[0]

            if hasattr(choice.message, "content") and choice.message.content:
                result["content"] = choice.message.content

            # 处理 reasoning_content（某些模型如 zai/glm 将内容放在这里）
            if hasattr(choice.message, "provider_specific_fields"):
                provider_fields = choice.message.provider_specific_fields
                if provider_fields and hasattr(provider_fields, "reasoning_content"):
                    if provider_fields.reasoning_content:
                        result["content"] = provider_fields.reasoning_content

            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    # 解析参数（处理某些提供商的 JSON 字符串）
                    parsed_args = _parse_tool_arguments(tool_call.function.arguments)
                    result["tool_calls"].append(
                        ToolCall(
                            name=tool_call.function.name,
                            arguments=parsed_args,
                            id=tool_call.id,
                        )
                    )
        elif hasattr(response, "content"):
            # Anthropic 风格的响应（内容块列表）
            for block in response.content:
                if block.type == "text":
                    result["content"] += block.text
                elif block.type == "tool_use":
                    result["tool_calls"].append(
                        ToolCall(
                            name=block.name,
                            arguments=block.input,
                            id=block.id,
                        )
                    )

        # 如果可用，添加使用信息
        if hasattr(response, "usage"):
            if hasattr(response.usage, "prompt_tokens"):
                result["usage"] = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                    if hasattr(response.usage, "completion_tokens")
                    else response.usage.output_tokens,
                }

        return result

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将 Message 对象转换为 litellm 格式。"""
        litellm_messages = []
        current_assistant_message = None

        for msg in messages:
            if msg.role == "system":
                litellm_messages.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                # 先添加任何待处理的助手消息
                if current_assistant_message:
                    litellm_messages.append(current_assistant_message)
                    current_assistant_message = None
                litellm_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                # 检查这是否是工具执行结果（启发式）
                if "工具执行结果" in msg.content or "文件已更新" in msg.content:
                    # 这是工具结果，作为用户消息处理
                    if current_assistant_message:
                        litellm_messages.append(current_assistant_message)
                        current_assistant_message = None
                    litellm_messages.append({"role": "user", "content": msg.content})
                else:
                    # 常规助手响应
                    if current_assistant_message:
                        litellm_messages.append(current_assistant_message)
                        current_assistant_message = None
                    current_assistant_message = {"role": "assistant", "content": msg.content}
            elif msg.role == "tool":
                # 工具结果 - 需要 tool_use_id
                if current_assistant_message:
                    litellm_messages.append(current_assistant_message)
                    current_assistant_message = None

                # 使用 Anthropic 风格的 tool_result 格式
                litellm_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )

        # 添加任何待处理的助手消息
        if current_assistant_message:
            litellm_messages.append(current_assistant_message)

        return litellm_messages

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """将 ToolDefinition 对象转换为 litellm 格式。"""
        litellm_tools = []

        for tool in tools:
            litellm_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": tool.parameters,
                            "required": list(tool.parameters.keys()),
                        },
                    },
                }
            )

        return litellm_tools

    def supports_tools(self) -> bool:
        """大多数现代 LLM 支持工具调用。"""
        return True
