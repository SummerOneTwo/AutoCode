"""
MCP Server 入口。

提供 14 个原子工具，基于 AutoCode 论文框架。
"""
import asyncio
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.base import Tool as BaseTool, ToolResult
from .tools.file_ops import FileReadTool, FileSaveTool
from .tools.solution import SolutionBuildTool, SolutionRunTool
from .tools.stress_test import StressTestRunTool
from .tools.problem import ProblemCreateTool, ProblemGenerateTestsTool, ProblemPackPolygonTool
from .tools.validator import ValidatorBuildTool, ValidatorSelectTool
from .tools.generator import GeneratorBuildTool, GeneratorRunTool
from .tools.checker import CheckerBuildTool
from .tools.interactor import InteractorBuildTool


# 创建 MCP Server 实例
app = Server("autocode-mcp")

# 所有工具实例
TOOLS: dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    """注册工具。"""
    TOOLS[tool.name] = tool


def register_all_tools() -> None:
    """注册所有工具。"""
    # File 工具组
    register_tool(FileReadTool())
    register_tool(FileSaveTool())

    # Solution 工具组
    register_tool(SolutionBuildTool())
    register_tool(SolutionRunTool())

    # Stress Test 工具组
    register_tool(StressTestRunTool())

    # Problem 工具组
    register_tool(ProblemCreateTool())
    register_tool(ProblemGenerateTestsTool())
    register_tool(ProblemPackPolygonTool())

    # Validator 工具组
    register_tool(ValidatorBuildTool())
    register_tool(ValidatorSelectTool())

    # Generator 工具组
    register_tool(GeneratorBuildTool())
    register_tool(GeneratorRunTool())

    # Checker 工具组
    register_tool(CheckerBuildTool())

    # Interactor 工具组
    register_tool(InteractorBuildTool())


@app.list_tools()
async def list_tools() -> list[Tool]:
    """返回所有可用工具。"""
    return [
        Tool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.input_schema,
        )
        for tool in TOOLS.values()
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """执行工具调用。"""
    if name not in TOOLS:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}",
        )]

    tool = TOOLS[name]
    try:
        result = await tool.execute(**arguments)
        return [TextContent(
            type="text",
            text=str(result.to_dict()),
        )]
    except Exception as e:
        error_result = ToolResult.fail(str(e))
        return [TextContent(
            type="text",
            text=str(error_result.to_dict()),
        )]


def main() -> None:
    """启动 MCP Server。"""
    register_all_tools()

    async def run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
