"""
AutoCode MCP 工具模块。
"""
from .base import Tool, ToolResult
from .file_ops import FileReadTool, FileSaveTool
from .solution import SolutionBuildTool, SolutionRunTool
from .stress_test import StressTestRunTool
from .problem import ProblemCreateTool, ProblemGenerateTestsTool, ProblemPackPolygonTool
from .validator import ValidatorBuildTool, ValidatorSelectTool
from .generator import GeneratorBuildTool, GeneratorRunTool
from .checker import CheckerBuildTool
from .interactor import InteractorBuildTool

__all__ = [
    "Tool",
    "ToolResult",
    "FileReadTool",
    "FileSaveTool",
    "SolutionBuildTool",
    "SolutionRunTool",
    "StressTestRunTool",
    "ProblemCreateTool",
    "ProblemGenerateTestsTool",
    "ProblemPackPolygonTool",
    "ValidatorBuildTool",
    "ValidatorSelectTool",
    "GeneratorBuildTool",
    "GeneratorRunTool",
    "CheckerBuildTool",
    "InteractorBuildTool",
]
