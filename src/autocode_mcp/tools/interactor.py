"""
Interactor 工具组 - 交互器。

基于论文 Algorithm 4: BUILDINTERACTOR 实现。
"""

from __future__ import annotations

import asyncio
import os

from ..utils.compiler import compile_cpp
from ..utils.platform import get_exe_extension
from .base import Tool, ToolResult
from .mixins import resolve_source


class InteractorBuildTool(Tool):
    """构建并验证交互器。"""

    @property
    def name(self) -> str:
        return "interactor_build"

    @property
    def description(self) -> str:
        return """构建并验证交互器。

        基于论文 Algorithm 4 实现:
        1. 保存代码到 problem_dir/files/interactor.cpp
        2. 编译生成 files/interactor.exe
        3. 运行变异测试验证区分能力
        4. 返回 pass_rate 和 fail_rate

        注意：此工具不生成代码，代码由 Client LLM 生成后传入。
        变异程序也应由 Client LLM 生成。
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
                "code": {
                    "type": "string",
                    "description": "C++ 源代码（与 source_path 二选一）",
                },
                "source_path": {
                    "type": "string",
                    "description": "源文件路径，相对于 problem_dir 或绝对路径。与 code 二选一，优先级高于 code",
                },
                "reference_solution_path": {
                    "type": "string",
                    "description": "参考解法路径（用于验证正确解能通过）",
                },
                "mutant_solutions": {
                    "type": "array",
                    "description": "变异解法路径列表（用于验证错误解被拒绝）",
                    "items": {"type": "string"},
                },
                "compiler": {
                    "type": "string",
                    "description": "编译器名称",
                    "default": "g++",
                },
            },
            "required": ["problem_dir"],
            "anyOf": [
                {"required": ["code"]},
                {"required": ["source_path"]},
            ],
        }

    async def execute(
        self,
        problem_dir: str,
        code: str | None = None,
        source_path: str | None = None,
        reference_solution_path: str | None = None,
        mutant_solutions: list[str] | None = None,
        compiler: str = "g++",
    ) -> ToolResult:
        """执行 Interactor 构建。"""
        resolved, err = resolve_source(problem_dir, code, source_path)
        if err is not None:
            return err
        assert resolved is not None

        os.makedirs(problem_dir, exist_ok=True)
        files_dir = os.path.join(problem_dir, "files")
        os.makedirs(files_dir, exist_ok=True)

        canonical_path = os.path.join(files_dir, "interactor.cpp")
        try:
            with open(canonical_path, "w", encoding="utf-8") as f:
                f.write(resolved.code)
        except Exception as e:
            return ToolResult.fail(f"Failed to save code: {str(e)}")

        binary_path = os.path.join(files_dir, f"interactor{get_exe_extension()}")

        compile_source = resolved.original_source_path or canonical_path
        include_dirs = [resolved.include_dir] if resolved.include_dir else None
        compile_result = await compile_cpp(compile_source, binary_path, compiler=compiler, include_dirs=include_dirs)

        if not compile_result.success:
            return ToolResult.fail(
                f"Compilation failed: {compile_result.error}",
                source_path=compile_source,
                canonical_path=canonical_path,
                compile_log=compile_result.stderr,
            )

        binary_size = os.path.getsize(binary_path) if os.path.exists(binary_path) else 0

        # 如果没有提供参考解和变异解，直接返回成功（但 pass_rate 为 0）
        if not reference_solution_path and not mutant_solutions:
            return ToolResult.ok(
                source_path=compile_source,
                canonical_path=canonical_path,
                binary_path=binary_path,
                binary_size=binary_size,
                compile_log=compile_result.stderr,
                pass_rate=0.0,
                fail_rate=0.0,
                pass_count=0,
                pass_total=0,
                fail_count=0,
                fail_total=0,
                message="Interactor built successfully (no validation performed)",
            )

        # 验证正确解通过率
        pass_count = 0
        pass_total = 0

        if reference_solution_path:
            # 检查参考解是否存在，不存在则报错而非静默跳过
            if not os.path.exists(reference_solution_path):
                return ToolResult.fail(
                    f"Reference solution not found: {reference_solution_path}",
                    source_path=compile_source,
                    canonical_path=canonical_path,
                    binary_path=binary_path,
                )
            pass_total = 1
            # 运行交互测试：参考解应该被接受
            test_result = await self._run_interactor_test(
                interactor_exe=binary_path, solution_exe=reference_solution_path, timeout=10
            )
            if test_result["verdict"] == "AC":
                pass_count = 1

        # 验证变异解被拒绝率
        fail_count = 0
        fail_total = len(mutant_solutions) if mutant_solutions else 0

        if mutant_solutions:
            for mutant_path in mutant_solutions:
                if os.path.exists(mutant_path):
                    # 运行交互测试：变异解应该被拒绝
                    test_result = await self._run_interactor_test(
                        interactor_exe=binary_path, solution_exe=mutant_path, timeout=10
                    )
                    # 交互器返回 WA 或其他非 AC 结果表示拒绝
                    if test_result.get("verdict") != "AC":
                        fail_count += 1

        # 计算通过率 - 没有测试时为 0，不是 1.0
        pass_rate = pass_count / pass_total if pass_total > 0 else 0.0
        fail_rate = fail_count / fail_total if fail_total > 0 else 0.0

        return ToolResult.ok(
            source_path=compile_source,
            canonical_path=canonical_path,
            binary_path=binary_path,
            binary_size=binary_size,
            compile_log=compile_result.stderr,
            pass_rate=pass_rate,
            fail_rate=fail_rate,
            pass_count=pass_count,
            pass_total=pass_total,
            fail_count=fail_count,
            fail_total=fail_total,
            message=f"Interactor built, pass_rate={pass_rate:.2%}, fail_rate={fail_rate:.2%}",
        )

    async def _run_interactor_test(
        self,
        interactor_exe: str,
        solution_exe: str,
        timeout: int = 10,
    ) -> dict:
        """
        运行交互测试，验证解法通过交互器。

        交互测试流程：
        1. 启动交互器进程
        2. 启动解法进程
        3. 在它们之间建立通信管道
        4. 交互器充当中间人，判断解法输出是否正确

        Args:
            interactor_exe: 交互器可执行文件路径
            solution_exe: 解法可执行文件路径
            timeout: 超时时间（秒）

        Returns:
            dict: 包含 verdict（判断结果）和详细信息
        """
        try:
            # 启动交互器
            interactor = await asyncio.create_subprocess_exec(
                interactor_exe,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 启动解法
            solution = await asyncio.create_subprocess_exec(
                solution_exe,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 建立通信管道
            # 交互器 stdin <-> solution stdout
            # 解法 stdin <-> interactor stdout
            # 这里简化处理：让解法和交互器都运行，等待完成

            try:
                # 创建通信任务和超时任务（命名以便识别）
                comm_task = asyncio.create_task(self._communicate(interactor, solution))
                sleep_task = asyncio.create_task(asyncio.sleep(timeout))
                sleep_task.set_name("sleep")

                # 等待任一进程完成
                done, pending = await asyncio.wait(
                    [comm_task, sleep_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # 检查是否超时
                timed_out = sleep_task in done

                if timed_out:
                    interactor.kill()
                    solution.kill()
                    await interactor.wait()
                    await solution.wait()
                    return {"verdict": "TLE", "reason": "Timeout"}

                # 获取通信结果
                if comm_task and not comm_task.cancelled():
                    result = comm_task.result()
                    if result:
                        return result

            except TimeoutError:
                interactor.kill()
                solution.kill()
                await interactor.wait()
                await solution.wait()
                return {"verdict": "TLE", "reason": "Timeout"}

            # 清理进程
            if interactor.returncode is None:
                interactor.kill()
            if solution.returncode is None:
                solution.kill()
            await asyncio.gather(interactor.wait(), solution.wait(), return_exceptions=True)

        except FileNotFoundError:
            return {"verdict": "RE", "reason": "Binary not found"}
        except Exception as e:
            return {"verdict": "RE", "reason": str(e)}

        # 如果走到这里，说明通信任务没有返回有效结果
        # 这通常表示进程异常终止或通信失败
        return {"verdict": "RE", "reason": "Interactor test failed to complete"}

    async def _communicate(
        self,
        interactor: asyncio.subprocess.Process,
        solution: asyncio.subprocess.Process,
    ) -> dict:
        """
        在交互器和解法之间建立双向通信管道。

        interactor.stdout -> solution.stdin
        solution.stdout -> interactor.stdin
        """

        async def pipe_data(reader, writer, name: str):
            """从 reader 读取数据并写入 writer"""
            try:
                while True:
                    data = await reader.read(4096)
                    if not data:
                        break
                    writer.write(data)
                    await writer.drain()
            except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError, OSError):
                pass

        pipe_tasks = []
        try:
            # 启动双向管道
            pipe_tasks = [
                asyncio.create_task(
                    pipe_data(interactor.stdout, solution.stdin, "interactor->solution")
                ),
                asyncio.create_task(
                    pipe_data(solution.stdout, interactor.stdin, "solution->interactor")
                ),
            ]

            # 等待任一进程完成 - 使用 create_task 避免弃用警告
            await asyncio.wait(
                [asyncio.create_task(interactor.wait()), asyncio.create_task(solution.wait())],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except NotImplementedError:
            # Windows 上可能不支持某些 asyncio 功能
            pass
        finally:
            # 取消管道任务
            for task in pipe_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # 清理进程
            for proc in [interactor, solution]:
                if proc.returncode is None:
                    try:
                        proc.kill()
                    except (ProcessLookupError, OSError):
                        pass
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2)
                except (TimeoutError, OSError):
                    pass

        # 根据交互器退出码判断结果
        # Interactor 返回码约定 (testlib.h):
        # 0 = AC, 1 = WA, 2 = PE, 3+ = Fail
        verdict_map = {0: "AC", 1: "WA", 2: "PE"}
        if interactor.returncode in verdict_map:
            return {"verdict": verdict_map[interactor.returncode], "reason": "..."}
        else:
            return {
                "verdict": "RE",
                "reason": f"Runtime error (exit code: {interactor.returncode})",
            }
