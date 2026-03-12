"""
Anthropic Claude 提供商实现。
"""
import os
from typing import List, Dict, Any, Optional
import anthropic

from .base import LLMProvider, Message, ToolCall, ToolDefinition


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM 提供商。"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-opus-4-6"):
        """
        初始化 Anthropic 提供商。

        Args:
            api_key: Anthropic API 密钥。如果为 None，从 ANTHROPIC_API_KEY 环境变量读取。
            model: 要使用的模型名称（如 "claude-opus-4-6", "claude-sonnet-4-6"）。
        """
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "未找到 ANTHROPIC_API_KEY。请设置环境变量或传入 api_key 参数。"
                )

        super().__init__(model)
        self.client = anthropic.Anthropic(api_key=api_key)

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        向 Anthropic Claude 发送聊天完成请求。

        Args:
            messages: Message 对象列表。
            tools: 可选的 ToolDefinition 对象列表。
            **kwargs: 额外参数（max_tokens、temperature 等）。

        Returns:
            包含 'content' 和可选的 'tool_calls' 的字典。
        """
        # 转换消息为 Anthropic 格式
        anthropic_messages = self._convert_messages(messages)

        # 转换工具为 Anthropic 格式
        anthropic_tools = None
        if tools:
            anthropic_tools = self._convert_tools(tools)

        # 设置默认参数
        params = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 404096),
        }

        # 如果提供了工具，添加工具
        if anthropic_tools:
            params["tools"] = anthropic_tools

        # 添加可选参数
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]

        # 发起 API 调用
        response = self.client.messages.create(**params)

        # 解析响应
        result = {"content": "", "tool_calls": []}

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
            result["usage"] = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

        return result

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将 Message 对象转换为 Anthropic 格式。"""
        anthropic_messages = []
        current_assistant_message = None

        for msg in messages:
            if msg.role == "system":
                anthropic_messages.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                # 如果有待处理的助手消息，先添加它
                if current_assistant_message:
                    anthropic_messages.append(current_assistant_message)
                    current_assistant_message = None
                anthropic_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                # 检查这是否是工具调用响应
                if "工具执行结果" in msg.content or "文件已更新" in msg.content:
                    # 这是工具结果，单独处理
                    if current_assistant_message:
                        anthropic_messages.append(current_assistant_message)
                        current_assistant_message = None
                    anthropic_messages.append({"role": "user", "content": msg.content})
                else:
                    # 助手文本响应
                    if current_assistant_message:
                        anthropic_messages.append(current_assistant_message)
                        current_assistant_message = None
                    current_assistant_message = {"role": "assistant", "content": msg.content}
            elif msg.role == "tool":
                # 工具结果 - 需要 tool_use_block_id
                if current_assistant_message:
                    anthropic_messages.append(current_assistant_message)
                    current_assistant_message = None
                anthropic_messages.append(
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
            anthropic_messages.append(current_assistant_message)

        return anthropic_messages

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """将 ToolDefinition 对象转换为 Anthropic 格式。"""
        anthropic_tools = []

        for tool in tools:
            anthropic_tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                }
            )

        return anthropic_tools

    def supports_tools(self) -> bool:
        """Anthropic Claude 支持工具调用。"""
        return True
