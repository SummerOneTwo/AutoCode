"""
LLM 提供商的基类。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """对话中的一条消息。"""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None  # 用于工具响应消息


@dataclass
class ToolCall:
    """来自 LLM 的工具调用。"""
    name: str
    arguments: Dict[str, Any]
    id: str


@dataclass
class ToolDefinition:
    """可被 LLM 调用的工具的定义。"""
    name: str
    description: str
    parameters: Dict[str, Any]


class LLMProvider(ABC):
    """LLM 提供商的抽象基类。"""

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        向 LLM 发送聊天完成请求。

        返回包含以下内容的字典：
        - 'content': LLM 的文本响应
        - 'tool_calls': 可选的 ToolCall 对象列表
        - 'usage': 可选的使用统计信息
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """检查提供商是否支持工具调用。"""
        pass
