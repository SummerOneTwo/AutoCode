"""
Stress test tool for comparing sol.cpp and brute.cpp outputs.
"""
import os
import sys
import subprocess
import tempfile
from typing import Dict, Any
from .base import Tool
from .compiler import CompileAllTool


class RunStressTestTool(Tool):
    """Tool for running stress tests to compare sol.cpp and brute.cpp outputs."""

    def __init__(
        self,
        work_dir: str,
        trials: int = 1000,
        n_max: int = 100,
        t_max: int = 3,
    ):
        super().__init__(
            name="run_stress_test",
            description=(
                f"运行对拍测试。编译所有文件并执行 {trials} 轮小数据测试。"
                "测试数据使用小规模参数（N <= {n_max}），确保暴力解法快速运行。"
            ),
            parameters={
                "trials": {
                    "type": "integer",
                    "description": f"测试轮数（默认 {trials}）",
                },
                "n_max": {
                    "type": "integer",
                    "description": f"生成的 N 最大值（默认 {n_max}，用于小数据测试）",
                },
                "t_max": {
                    "type": "integer",
                    "description": f"生成的 T 最大值（默认 {t_max}）",
                },
            },
        )
        self.work_dir = os.path.abspath(work_dir)
        self.default_trials = trials
        self.default_n_max = n_max
        self.default_t_max = t_max

    def execute(self, trials: int = None, n_max: int = None, t_max: int = None) -> Dict[str, Any]:
        """Run stress test comparing sol.cpp and brute.cpp."""
        # Use defaults if not provided
        if trials is None:
            trials = self.default_trials
        if n_max is None:
            n_max = self.default_n_max
        if t_max is None:
            t_max = self.default_t_max

        # Validate parameters
        error = self.validate_parameters({"trials": trials, "n_max": n_max, "t_max": t_max})
        if error:
            return {"success": False, "error": error}

        # 1. Compile all source files
        compile_tool = CompileAllTool(self.work_dir)
        compile_result = compile_tool.execute()

        if not compile_result["success"]:
            return {
                "success": False,
                "error": "编译失败，无法运行对拍测试",
                "compile_result": compile_result,
            }

        # 2. Determine executable extension
        exe_ext = ".exe" if sys.platform == "win32" else ""

        # 3. Check for required executables
        gen_exe = os.path.join(self.work_dir, f"gen{exe_ext}")
        val_exe = os.path.join(self.work_dir, f"val{exe_ext}")
        sol_exe = os.path.join(self.work_dir, f"sol{exe_ext}")
        brute_exe = os.path.join(self.work_dir, f"brute{exe_ext}")

        if not os.path.exists(gen_exe):
            return {
                "success": False,
                "error": f"找不到生成器: gen{exe_ext}",
                "compile_result": compile_result,
            }

        # 4. Run stress test
        failed_round = None
        last_input_data = None
        sol_output = None
        brute_output = None
        validator_failed = False

        with tempfile.TemporaryDirectory(dir=self.work_dir) as temp_dir:
            input_path = os.path.join(temp_dir, "input.txt")
            sol_out_path = os.path.join(temp_dir, "sol.out")
            brute_out_path = os.path.join(temp_dir, "brute.out")

            for i in range(1, trials + 1):
                # 1.1 Generate input data
                # gen.exe <seed> <type> <n_min> <n_max> <t_min> <t_max>
                # type=1 for tiny data (small N)
                try:
                    with open(input_path, "w") as f:
                        gen_result = subprocess.run(
                            [gen_exe, str(i), "1", "1", str(n_max), "1", str(t_max)],
                            stdout=f,
                            stderr=subprocess.PIPE,
                            timeout=30,
                        )
                        if gen_result.returncode != 0:
                            return {
                                "success": False,
                                "error": f"生成器在第 {i} 轮失败",
                                "round": i,
                                "gen_stderr": gen_result.stderr.decode("utf-8", errors="ignore"),
                            }
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "error": f"生成器在第 {i} 轮超时",
                        "round": i,
                    }

                # 1.2 Validate input data (if val.exe exists)
                if os.path.exists(val_exe):
                    with open(input_path, "r") as f:
                        val_result = subprocess.run(
                            [val_exe],
                            stdin=f,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=30,
                        )
                        if val_result.returncode != 0:
                            validator_failed = True
                            with open(input_path, "r") as f_in:
                                last_input_data = f_in.read()
                            failed_round = i
                            break

                # 1.3 Run sol.cpp
                with open(input_path, "r") as f_in, open(sol_out_path, "w") as f_out:
                    try:
                        sol_result = subprocess.run(
                            [sol_exe],
                            stdin=f_in,
                            stdout=f_out,
                            stderr=subprocess.PIPE,
                            timeout=30,
                        )
                        if sol_result.returncode != 0:
                            return {
                                "success": False,
                                "error": f"标准解法在第 {i} 轮失败",
                                "round": i,
                                "sol_stderr": sol_result.stderr.decode("utf-8", errors="ignore"),
                            }
                    except subprocess.TimeoutExpired:
                        return {
                            "success": False,
                            "error": f"标准解法在第 {i} 轮超时",
                            "round": i,
                        }

                # 1.4 Run brute.cpp
                with open(input_path, "r") as f_in, open(brute_out_path, "w") as f_out:
                    try:
                        brute_result = subprocess.run(
                            [brute_exe],
                            stdin=f_in,
                            stdout=f_out,
                            stderr=subprocess.PIPE,
                            timeout=30,
                        )
                        if brute_result.returncode != 0:
                            return {
                                "success": False,
                                "error": f"暴力解法在第 {i} 轮失败",
                                "round": i,
                                "brute_stderr": brute_result.stderr.decode("utf-8", errors="ignore"),
                            }
                    except subprocess.TimeoutExpired:
                        return {
                            "success": False,
                            "error": f"暴力解法在第 {i} 轮超时（可能是 N 过大）",
                            "round": i,
                            "suggestion": "尝试减小 n_max 参数以使用更小的测试数据",
                        }

                # 1.5 Compare outputs
                with open(sol_out_path, "r") as f1, open(brute_out_path, "r") as f2:
                    sol_output = f1.read().strip()
                    brute_output = f2.read().strip()

                    if sol_output != brute_output:
                        with open(input_path, "r") as f_in:
                            last_input_data = f_in.read()
                        failed_round = i
                        break

        # 5. Return results
        if failed_round:
            return {
                "success": False,
                "error": (
                    f"答案不一致，轮次 {failed_round}"
                    if not validator_failed
                    else f"验证器失败，轮次 {failed_round}"
                ),
                "round": failed_round,
                "input_data": last_input_data,
                "sol_output": sol_output,
                "brute_output": brute_output,
                "completed_rounds": failed_round - 1,
                "total_rounds": trials,
            }

        return {
            "success": True,
            "message": f"全部 {trials} 轮测试通过",
            "completed_rounds": trials,
            "total_rounds": trials,
        }


class QuickStressTestTool(Tool):
    """Tool for running a quick stress test (fewer rounds) for faster iteration."""

    def __init__(self, work_dir: str):
        super().__init__(
            name="quick_stress_test",
            description=(
                "运行快速对拍测试（10 轮小数据）。用于快速验证代码逻辑。"
                "适用于调试阶段。"
            ),
            parameters={},
        )
        self.work_dir = os.path.abspath(work_dir)

    def execute(self) -> Dict[str, Any]:
        """Run a quick stress test."""
        stress_tool = RunStressTestTool(self.work_dir, trials=10, n_max=20, t_max=1)
        return stress_tool.execute()
