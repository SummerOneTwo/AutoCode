"""
Solution 工具组 - 解法构建和运行。
"""

import os
from typing import Literal

from ..utils.platform import get_exe_extension
from .base import Tool, ToolResult
from .mixins import BuildToolMixin, RunToolMixin


class SolutionBuildTool(Tool, BuildToolMixin):
    """构建并编译解法。"""

    @property
    def name(self) -> str:
        return "solution_build"

    @property
    def description(self) -> str:
        return """构建并编译解法代码。

        基于论文框架，支持：
        - sol.cpp: 标准解法（最优时间复杂度）
        - brute.cpp: 暴力解法（用于验证）

        前置条件：
        1. 已运行 problem_create 创建题目目录

        建议下一步：
        - 构建 brute.cpp 后运行 stress_test_run 验证解法正确性
        - 构建 sol.cpp 后运行 generator_build 构建数据生成器
        """

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "problem_dir": {
                    "type": "string",
                    "description": "题目目录路径",
                },
                "solution_type": {
                    "type": "string",
                    "enum": ["sol", "brute"],
                    "description": "解法类型：sol（标准解法）或 brute（暴力解法）",
                },
                "code": {
                    "type": "string",
                    "description": "C++ 源代码（与 source_path 二选一）",
                },
                "source_path": {
                    "type": "string",
                    "description": "源文件路径，相对于 problem_dir 或绝对路径。与 code 二选一，优先级高于 code",
                },
                "compiler": {
                    "type": "string",
                    "description": "编译器名称",
                    "default": "g++",
                },
            },
            "required": ["problem_dir", "solution_type"],
            "anyOf": [
                {"required": ["code"]},
                {"required": ["source_path"]},
            ],
        }

    async def execute(
        self,
        problem_dir: str,
        solution_type: Literal["sol", "brute"],
        code: str | None = None,
        source_path: str | None = None,
        compiler: str = "g++",
    ) -> ToolResult:
        """执行解法构建。"""
        # 解析源代码：source_path 优先于 code
        source_dir = None
        if source_path:
            if not os.path.isabs(source_path):
                source_path = os.path.join(problem_dir, source_path)
            if not os.path.exists(source_path):
                return ToolResult.fail(f"Source file not found: {source_path}")
            try:
                with open(source_path, encoding="utf-8") as f:
                    code = f.read()
            except UnicodeDecodeError:
                try:
                    with open(source_path, encoding="latin-1") as f:
                        code = f.read()
                except Exception as e:
                    return ToolResult.fail(f"Failed to read source file: {e}")
            source_dir = os.path.dirname(os.path.abspath(source_path))
        elif code is None:
            return ToolResult.fail("Either 'code' or 'source_path' must be provided")

        # 确保目录存在
        os.makedirs(problem_dir, exist_ok=True)

        # 保存到 solutions/ 子目录
        solutions_dir = os.path.join(problem_dir, "solutions")
        os.makedirs(solutions_dir, exist_ok=True)

        # 确定文件名
        source_name = f"{solution_type}.cpp"
        source_path = os.path.join(solutions_dir, source_name)

        # 保存代码
        try:
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return ToolResult.fail(f"Failed to save code: {str(e)}")

        # 编译
        exe_ext = get_exe_extension()
        binary_name = f"{solution_type}{exe_ext}"
        binary_path = os.path.join(solutions_dir, binary_name)

        include_dirs = [source_dir] if source_dir else None
        result = await self.build(source_path, binary_path, compiler=compiler, include_dirs=include_dirs)

        if not result.success:
            return ToolResult.fail(
                f"Compilation failed: {result.error}",
                source_path=source_path,
                compile_log=result.stderr,
            )

        return ToolResult.ok(
            source_path=source_path,
            binary_path=binary_path,
            compile_log=result.stderr,
            message=f"Successfully built {solution_type}",
        )


class SolutionRunTool(Tool, RunToolMixin):
    """运行解法。"""

    @property
    def name(self) -> str:
        return "solution_run"

    @property
    def description(self) -> str:
        return """运行已编译的解法。

        在指定输入上运行解法，返回输出和执行时间。
        用于验证解法正确性或生成答案文件。

        前置条件：
        1. 已运行 solution_build 构建解法

        建议下一步：
        - 如果验证通过，继续构建 generator
        - 如果验证失败，修复解法代码
        """

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "problem_dir": {
                    "type": "string",
                    "description": "题目目录路径",
                },
                "solution_type": {
                    "type": "string",
                    "enum": ["sol", "brute"],
                    "description": "解法类型：sol 或 brute",
                },
                "input_data": {
                    "type": "string",
                    "description": "输入数据",
                },
                "timeout": {
                    "type": "integer",
                    "description": "执行超时（秒）",
                    "default": 30,
                },
            },
            "required": ["problem_dir", "solution_type", "input_data"],
        }

    async def execute(
        self,
        problem_dir: str,
        solution_type: Literal["sol", "brute"],
        input_data: str,
        timeout: int = 30,
    ) -> ToolResult:
        """执行解法运行。"""
        # 确定二进制文件路径 - 优先查找 solutions/ 子目录
        exe_ext = get_exe_extension()
        binary_path = os.path.join(problem_dir, "solutions", f"{solution_type}{exe_ext}")

        # 如果子目录没有，检查根目录（向后兼容）
        if not os.path.exists(binary_path):
            binary_path = os.path.join(problem_dir, f"{solution_type}{exe_ext}")

        if not os.path.exists(binary_path):
            return ToolResult.fail(
                f"Binary not found: {solution_type}. Please run solution_build first."
            )

        # 运行
        result = await self.run(
            binary_path, input_data, problem_dir, solution_type, timeout=timeout
        )

        if result.timed_out:
            return ToolResult.fail(
                f"Execution timed out after {timeout}s",
                stdout=result.stdout,
                stderr=result.stderr,
                time_ms=result.time_ms,
            )

        if not result.success:
            return ToolResult.fail(
                f"Execution failed with return code {result.return_code}",
                stdout=result.stdout,
                stderr=result.stderr,
                time_ms=result.time_ms,
            )

        return ToolResult.ok(
            stdout=result.stdout,
            stderr=result.stderr,
            time_ms=result.time_ms,
            return_code=result.return_code,
        )
