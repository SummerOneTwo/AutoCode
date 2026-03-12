"""
C++ compiler tool.
"""
import os
import sys
import subprocess
from typing import Dict, Any
from .base import Tool


class CompileCppTool(Tool):
    """Tool for compiling C++ source files."""

    def __init__(self, work_dir: str, compiler: str = "g++"):
        super().__init__(
            name="compile_cpp",
            description=(
                "编译 C++ 源文件。支持 Windows 和 Linux。"
                "使用 C++2C 标准和 O2 优化。"
            ),
            parameters={
                "source_file": {
                    "type": "string",
                    "description": "源文件名（如 gen.cpp, sol.cpp, val.cpp, brute.cpp）",
                },
            },
        )
        self.work_dir = os.path.abspath(work_dir)
        self.compiler = compiler

    def execute(self, source_file: str) -> Dict[str, Any]:
        """Compile a C++ source file."""
        # Validate parameters
        error = self.validate_parameters({"source_file": source_file})
        if error:
            return {"success": False, "error": error}

        # Check for .cpp extension
        if not source_file.endswith(".cpp"):
            return {
                "success": False,
                "error": f"Source file must have .cpp extension: {source_file}",
            }

        # Build source path
        src_path = os.path.join(self.work_dir, source_file)

        # Check if source file exists
        if not os.path.exists(src_path):
            return {
                "success": False,
                "error": f"Source file not found: {source_file}",
                "path": src_path,
            }

        # Determine executable extension
        exe_ext = ".exe" if sys.platform == "win32" else ""

        # Build executable path
        base_name = os.path.splitext(source_file)[0]
        exe_path = os.path.join(self.work_dir, base_name + exe_ext)

        # Build compile command
        cmd = [
            self.compiler,
            "-std=c++2c",
            "-O2",
            src_path,
            "-o",
            exe_path,
        ]

        try:
            # Run compiler
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.work_dir,
                timeout=60,  # 60 second timeout
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Compilation failed for {source_file}",
                    "returncode": result.returncode,
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "command": " ".join(cmd),
                }

            return {
                "success": True,
                "exe_path": exe_path,
                "source_file": source_file,
                "message": f"编译成功: {source_file} -> {base_name{exe_ext}}",
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Compilation timeout for {source_file}",
                "command": " ".join(cmd),
            }
        except OSError as e:
            return {
                "success": False,
                "error": f"Failed to run compiler {self.compiler}: {str(e)}",
            }


class CompileAllTool(Tool):
    """Tool for compiling all required C++ source files."""

    def __init__(self, work_dir: str, compiler: str = "g++"):
        super().__init__(
            name="compile_all",
            description=(
                "编译所有需要的 C++ 源文件（gen.cpp, val.cpp, sol.cpp, brute.cpp）。"
                "通常在运行对拍测试前调用此工具。"
            ),
            parameters={},
        )
        self.work_dir = os.path.abspath(work_dir)
        self.compiler = compiler

    def execute(self) -> Dict[str, Any]:
        """Compile all required source files."""
        sources = ["gen.cpp", "val.cpp", "sol.cpp", "brute.cpp"]

        results = {}
        errors = []
        success = True

        for source in sources:
            src_path = os.path.join(self.work_dir, source)

            # Skip if source file doesn't exist
            if not os.path.exists(src_path):
                results[source] = {
                    "success": False,
                    "skipped": True,
                    "message": f"跳过（文件不存在）: {source}",
                }
                continue

            # Compile the file
            compile_tool = CompileCppTool(self.work_dir, self.compiler)
            result = compile_tool.execute(source)

            results[source] = result

            if not result["success"]:
                success = False
                errors.append({
                    "source": source,
                    "error": result.get("error", "Unknown error"),
                })

        if success:
            compiled = [s for s, r in results.items() if r["success"] and not r.get("skipped", False)]
            return {
                "success": True,
                "results": results,
                "compiled_files": compiled,
                "message": f"编译成功: {', '.join(compiled)}",
            }
        else:
            return {
                "success": False,
                "error": "部分或全部源文件编译失败",
                "results": results,
                "errors": errors,
            }
