"""
工具基类。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Tool(ABC):
    """Agent 可使用的工具的基类。"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        使用给定参数执行工具。

        Returns:
            至少包含 'success' (bool) 键的字典。
            可能包含 'error'、'message'、'path' 等其他键。
        """
        pass

    def to_definition(self) -> Dict[str, Any]:
        """转换为 LLM 的工具定义格式。"""
        return {
            "type": "object",
            "properties": self.parameters,
            "required": list(self.parameters.keys()),
        }

    def validate_parameters(self, params: Dict[str, Any]) -> Optional[str]:
        """
        验证提供的参数。

        Returns:
            如果有效则返回 None，如果无效则返回错误消息字符串。
        """
        for param_name, param_info in self.parameters.items():
            if param_name not in params:
                return f"缺少必需参数: {param_name}"

            param_type = param_info.get("type", "string")
            value = params[param_name]

            if param_type == "string" and not isinstance(value, str):
                return f"参数 {param_name} 必须是字符串"
            elif param_type == "integer" and not isinstance(value, int):
                return f"参数 {param_name} 必须是整数"
            elif param_type == "boolean" and not isinstance(value, bool):
                return f"参数 {param_name} 必须是布尔值"
            elif param_type == "array" and not isinstance(value, list):
                return f"参数 {param_name} 必须是数组"

        return None
