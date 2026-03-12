"""
OpenAI 提供商实现。
"""
import os
from typing import List, Dict, Any, Optional
from .base import LLMProvider, Message, ToolCall, ToolDefinition


class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM 提供商。"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        初始化 OpenAI 提供商。

        Args:
            api_key: OpenAI API 密钥。如果为 None，从 OPENAI_API_KEY 环境变量读取。
            model: 要使用的模型名称（如 "gpt-4o", "gpt-4-turbo"）。
        """
        try:
            import openaiari
        except ImportError:
            raise ImportError(
                "OpenAI 提供商需要 'openai' 包。"
                "请安装：pip install openai"
            )

        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "未找到 OPENAI_API_KEY。请设置环境变量或传入 api_key 参数。"
                )

        super().__init__(model)
        self.client = openai.OpenAI(api_key=api_key)

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) ) -> Dict[str, Any]:
        """
        向 OpenAI 发送聊天完成请求。

        Args:
            messages: Message 对象列表。
            tools: 可选的 ToolDefinition 对象列表。
            **kwargs: 额外参数（max_tokens、temperature 等）。

        Returns:
            包含 'content' 和可选的 'tool_calls' 的字典。
        """
        # 转换消息为 OpenAI 格式
        openai_messages = self._convert_messages(messages)

        # 转换工具为 OpenAI 格式
        openai_tools = None
        if tools:
            openai_tools = self._convert_tools(tools)

        # 设置默认参数
        params = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", 404096),
        }

        # 如果提供了工具，添加工具
        if openai_tools:
            params["tools"] = openai_tools

        # 添加可选参数
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]

        # 发起 API 调用
        response = self.client.chat.completions.create(**params)

        # 解析响应
        result = {"content": "", "tool_calls": []}

        choice = response.choices[0]

        if choice.message.content:
            result["content"] = choice.message.content

        if choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                result["tool_calls"].append(
                    ToolCall(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                        id=tool_call.id,
                    )
                )

        # 添加使用信息
        if hasattr(response, "usage"):
            result["usage"] = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        return result

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将 Message 对象转换为 OpenAI 格式。"""
        openai_messages = []
        for msg in messages:
            if msg.role in ["system", "user", "assistant"]:
                openai_messages.append({"role": msg.role, "content": msg.content})
            elif msg.role == "tool":
                # OpenAI 使用不同的 tool_result 类型
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content,
                    }
                )

        return openai_messages

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """将 ToolDefinition 对象转换为 OpenAI 格式。"""
        openai_tools = []
        for tool in tools:
            openai_tools.append(
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

        return openai_tools

    def supports_tools(self) -> bool:
        """OpenAI GPT 支持工具调用。"""
        return True
