"""
Test data generation tool.
"""
import os
import sys
import subprocess
import shutil
from typing import Dict, Any
from .base import Tool
from .compiler import CompileCppTool


class GenerateTestsTool(Tool):
    """Tool for generating final test data (01.in ~ 20.in)."""

    def __init__(
        self,
        work_dir: str,
        test_count: int = 20,
    ):
        super().__init__(
            name="generate_tests",
            description=(
                f"生成最终测试数据（01.in ~ {test_count:02d}.in 及对应的 .ans 文件）。"
                "需要已编译的 gen.exe 和 sol.exe。"
                "生成的测试数据会保存在 tests/ 目录下。"
            ),
            parameters={
                "test_count": {
                    "type": "integer",
                    "description": f"测试数据组数（默认 {test_count}）",
                },
            },
        )
        self.work_dir = os.path.abspath(work_dir)
        self.default_test_count = test_count

    def execute(self, test_count: int = None) -> Dict[str, Any]:
        """Generate test data files."""
        # Use default if not provided
        if test_count is None:
            test_count = self.default_test_count

        # Validate parameters
        error = self.validate_parameters({"test_count": test_count})
        if error:
            return {"success": False, "error": error}

        # Check work directory structure
        if not os.path.exists(os.path.join(self.work_dir, "files")):
            return {
                "success": False,
                "error": "找不到 files/ 目录，请先运行 pack_polygon_to_format 或手动创建目录结构",
            }

        if not os.path.exists(os.path.join(self.work_dir, "solutions")):
            return {
                "success": False,
                "error": "找不到 solutions/ 目录",
            }

        # Determine executable extension
        exe_ext = ".exe" if sys.platform == "win32" else ""

        # Check for executables
        gen_exe = os.path.join(self.work_dir, "files", f"gen{exe_ext}")
        sol_exe = os.path.join(self.work_dir, "solutions", f"sol{exe_ext}")

        if not os.path.exists(gen_exe):
            # Try to compile gen.cpp
            gen_cpp = os.path.join(self.work_dir, "files", "gen.cpp")
            if os.path.exists(gen_cpp):
                compile_tool = CompileCppTool(os.path.join(self.work_dir, "files"))
                result = compile_tool.execute("gen.cpp")
                if not result["success"]:
                    return {
                        "success": False,
                        "error": f"无法编译 gen.cpp: {result.get('error')}",
                    }
            else:
                return {
                    "success": False,
                    "error": f"找不到 gen.exe 或 gen.cpp",
                }

        if not os.path.exists(sol_exe):
            # Try to compile sol.cpp
            sol_cpp = os.path.join(self.work_dir, "solutions", "sol.cpp")
            if os.path.exists(sol_cpp):
                compile_tool = CompileCppTool(os.path.join(self.work_dir, "solutions"))
                result = compile_tool.execute("sol.cpp")
                if not result["success"]:
                    return {
                        "success": False,
                        "error": f"无法编译 sol.cpp: {result.get('error')}",
                    }
            else:
                return {
                    "success": False,
                    "error": f"找不到 sol.exe 或 sol.cpp",
                }

        # Create tests directory
        tests_dir = os.path.join(self.work_dir, "tests")
        if os.path.exists(tests_dir):
            shutil.rmtree(tests_dir)
        os.makedirs(tests_dir)

        # Define test generation commands
        # Each command is a tuple: (seed_offset, type, n_min, n_max, t_min, t_max, count)
        # type: 1=小数据, 2=随机, 3=大值, 4=边界, 5=反hack

        test_configs = []
        config_id = 1

        # 1. 小数据 (N <= 10)
        test_configs.extend([("1", "1", "1", "10", "1", "3")] * 3)
        config_id += 3

        # 2. 随机数据
        test_configs.extend([
            ("2", "2", "10", "100", "1", "3"),
            ("2", "2", "100", "1000", "1", "3"),
            ("2", "2", "1000", "5000", "1", "3"),
            ("2", "2", "5000", "10000", "1", "3"),
            ("2", "2", "100", "10000", "2", "5"),
            ("2", "2", "10", "10000", "1", "3"),
            ("2", "2", "1000", "10000", "1", "2"),
        ])
        config_id += 7

        # 3. 大数据
        test_configs.extend([
            ("3", "3", "100000", "200000", "1", "1"),
            ("3", "3", "150000", "200000", "1", "1"),
            ("3", "3", "190000", "200000", "1", "1"),
            ("3", "3", "199000", "200000", "1", "1"),
            ("3", "3", "200000", "200000", "1", "1"),
        ])
        config_id += 5

        # 4. 边界数据
        test_configs.extend([
            ("4", "4", "10", "50", "1", "3"),
            ("4", "4", "10", "100", "1", "3"),
            ("4", "4", "50", "200", "1", "3"),
        ])
        config_id += 3

        # 5. 反hack数据
        test_configs.extend([
            ("5", "5", "50", "200", "1", "3"),
            ("5", "5", "100", "500", "1", "3"),
        ])

        # Generate tests
        generated_tests = []
        errors = []

        for i, config in enumerate(test_configs[:test_count], 1):
            test_file = os.path.join(tests_dir, f"{i:02d}.in")
            ans_file = os.path.join(tests_dir, f"{i:02d}.ans")

            # gen.exe <seed> <type> <n_min> <n_max> <t_min> <t_max>
            try:
                # Generate input
                with open(test_file, "w") as f:
                    gen_cmd = [gen_exe, str(i)] + list(config)
                    result = subprocess.run(
                        gen_cmd,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        timeout=60,
                    )
                    if result.returncode != 0:
                        errors.append((i, f"生成器失败: {result.stderr.decode('utf-8', errors='ignore')}"))
                        continue

                # Generate answer
                with open(test_file, "r") as f_in, open(ans_file, "w") as f_out:
                    result = subprocess.run(
                        [sol_exe],
                        stdin=f_in,
                        stdout=f_out,
                        stderr=subprocess.PIPE,
                        timeout=60,
                    )
                    if result.returncode != 0:
                        errors.append((i, f"标程失败: {result.stderr.decode('utf-8', errors='ignore')}"))
                        continue

                generated_tests.append(i)

            except subprocess.TimeoutExpired as e:
                errors.append((i, f"超时: {str(e)}"))
            except Exception as e:
                errors.append((i, f"错误: {str(e)}"))

        if len(generated_tests) == test_count:
            return {
                "success": True,
                "message": f"成功生成 {len(generated_tests)} 组测试数据",
                "tests_dir": tests_dir,
                "generated_tests": generated_tests,
            }
        else:
            return {
                "success": False,
                "error": f"部分测试数据生成失败。成功: {len(generated_tests)}/{test_count}",
                "generated_tests": generated_tests,
                "errors": errors,
                "tests_dir": tests_dir,
            }
