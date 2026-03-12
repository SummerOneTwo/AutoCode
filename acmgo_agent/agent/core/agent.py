"""
ACMGO 出题 Agent 主类。

实现带自愈机制的 ReAct 循环。
"""
import os
from typing import List, Dict, Any, Optional, Callable

from ..providers.base import LLMProvider, Message, ToolCall
from ..core.state import AgentState, WorkflowStage, StageResult
from ..prompts.system import get_system_prompt
from ..prompts.stages import get_stage_prompt, get_stress_test_failure_prompt


class ProblemSetterAgent:
    """
    用于自动化竞赛编程出题的 AI Agent。

    使用带工具调用和自愈机制的 ReAct 循环。
    """

    def __init__(
        self,
        provider: LLMProvider,
        work_dir: str,
        max_retries: int = 3,
        auto_progress: bool = False,
        verbose: bool = True,
    ):
        """
        初始化 Agent。

        Args:
            provider: LLM 提供商实例。
            work_dir: 题目工作目录。
            max_retries: 自愈最大重试次数。
            auto_progress: 如果为 True，自动进入下一步。
                        如果为 False，在阶段间等待用户确认。
            verbose: 如果为 True，打印详细进度信息。
        """
        self.provider = provider
        self.work_dir = os.path.abspath(work_dir)
        self.max_retries = max_retries
        self.auto_progress = auto_progress
        self.verbose = verbose

        # 确保工作目录存在
        os.makedirs(self.work_dir, exist_ok=True)

        # 初始化状态
        self.state = AgentState()
        self.state.max_retries = max_retries

        # 初始化工具
        self.tools = self._init_tools()

        # 钩子
        self.before_stage_hook: Optional[Callable] = None
        self.after_stage_hook: Optional[Callable] = None

        # 自定义系统提示词
        self.custom_system_prompt = None

    def _init_tools(self) -> Dict[str, Any]:
        """初始化所有可用工具。"""
        from ..tools import (
            SaveFileTool,
            ReadFileTool,
            ListFilesTool,
            CompileCppTool,
            CompileAllTool,
            RunStressTestTool,
            QuickStressTestTool,
            GenerateTestsTool,
            PackPolygonTool,
            SetupDevTool,
        )

        return {
            "save_file": SaveFileTool(self.work_dir),
            "read_file": ReadFileTool(self.work_dir),
            "list_files": ListFilesTool(self.work_dir),
            "compile_cpp": CompileCppTool(self.work_dir),
            "compile_all": CompileAllTool(self.work_dir),
            "run_stress_test": RunStressTestTool(self.work_dir),
            "quick_stress_test": QuickStressTestTool(self.work_dir),
            "generate_tests": GenerateTestsTool(self.work_dir),
            "pack_polygon_to_format": PackPolygonTool(self.work_dir),
            "setup_dev": SetupDevTool(self.work_dir),
        }

    def register_tool(self, name: str, tool: Any) -> None:
        """注册自定义工具。"""
        self.tools[name] = tool

    def set_custom_system_prompt(self, prompt: str) -> None:
        """设置自定义系统提示词。"""
        self.custom_system_prompt = prompt

    def set_hooks(
        self,
        before_stage: Optional[Callable] = None,
        after_stage: Optional[Callable] = None,
    ) -> None:
        """设置阶段生命周期钩子。"""
        self.before_stage_hook = before_stage
        self.after_stage_hook = after_stage

    def run(self, problem_description: str) -> Dict[str, Any]:
        """
        执行完整的 6 步工作流程。

        Args:
            problem_description: 题目的核心算法描述。

        Returns:
            包含 'status' ('success' 或 'failed') 和结果的字典。
        """
        self._log(f"开始出题，工作目录: {self.work_dir}")
        self._log(f"题目核心算法: {problem_description}")

        # 在状态中保存题目描述
        self.state.problem_description = problem_description

        # 构建系统提示词
        system_prompt = get_system_prompt(self.custom_system_prompt)

        # 初始化对话
        messages = [Message("system", system_prompt)]
        user_message = f"我们开始出题，核心算法是：{problem_description}"
        messages.append(Message("user", user_message))

        # 从阶段 1 开始
        self.state.set_current_stage(WorkflowStage.STATEMENT)

        # ReAct 循环
        while not self.state.is_complete():
            if self.state.current_stage is None:
                # 所有阶段已完成
                break

            # 调用阶段前钩子
            if self.before_stage_hook:
                self.before_stage_hook(
                    self.state.current_stage.value,
                    {"work_dir": self.work_dir, "progress": self.state.get_progress()},
                )

            # 执行当前阶段
            stage_result = self._execute_stage(messages, self.state.current_stage)

            # 标记阶段完成
            if stage_result.success:
                self.state.mark_stage_complete(self.state.current_stage, stage_result)
                self._log(
                    f"完成阶段: {self.state.current_stage.display_name} "
                    f"({self.state.get_progress():.1f}%)"
                )

                # 调用阶段后钩子
                if self.after_stage_hook:
                    self.after_stage_hook(
                        self.state.current_stage.value,
                        stage_result.__dict__,
                        {"work_dir": self.work_dir, "progress": self.state.get_progress()},
                    )

                # 进入下一阶段
                next_stage = self.state.current_stage.next_stage
                if next_stage:
                    self.state.set_current_stage(next_stage)

                    # 为下一阶段添加阶段提示词
                    stage_prompt = get_stage_prompt(next_stage.value)
                    if stage_prompt:
                        messages.append(Message("user", stage_prompt))

            else:
                # 阶段失败
                self._log(f"阶段失败: {self.state.current_stage.display_name}")
                return {
                    "status": "failed",
                    "stage": self.state.current_stage.value,
                    "error": stage_result.message,
                    "work_dir": self.work_dir,
                }

        # 所有阶段完成
        self._log("出题完成！")
        return {
            "status": "success",
            "work_dir": self.work_dir,
            "stage_results": {k.value: v.__dict__ for k, v in self.state.stage_results.items()},
        }

    def _execute_stage(
        self, messages: List[Message], stage: WorkflowStage
    ) -> StageResult:
        """
        执行单个工作流程阶段。

        Args:
            messages: 对话消息。
            stage: 当前工作流程阶段。

        Returns:
            表示成功/失败的 StageResult。
        """
        self._log(f"执行阶段: {stage.display_name}")

        # 对于阶段 1-4，让 LLM 生成文件
        if stage in [
            WorkflowStage.STATEMENT,
            WorkflowStage.SOLUTIONS,
            WorkflowStage.VALIDATOR,
            WorkflowStage.GENERATOR,
        ]:
            return self._llm_generation_stage(messages, stage)

        # 阶段 5：带自愈的压力测试
        elif stage == WorkflowStage.STRESS_TEST:
            return self._stress_test_stage(messages)

        # 阶段 6：打包
        elif stage == WorkflowStage.PACKAGE:
            return self._package_stage(messages)

        else:
            return StageResult(
                stage=stage,
                success=False,
                message=f"未知阶段: {stage.value}",
            )

    def _llm_generation_stage(
        self, messages: List[Message], stage: WorkflowStage
    ) -> StageResult:
        """让 LLM 为当前阶段生成文件。"""
        # 调用 LLM 获取工具调用
        response = self.provider.chat(messages, tools=self._get_tool_definitions())

        files_created = []

        if "tool_calls" in response and response["tool_calls"]:
            for tool_call in response["tool_calls"]:
                # 执行工具
                tool_result = self._execute_tool(tool_call)

                # 添加到对话
                messages.append(Message("assistant", f"调用工具: {tool_call.name}"))
                messages.append(Message("user", f"工具执行结果: {tool_result}"))

                # 追踪创建的文件
                if tool_result.get("success"):
                    if "path" in tool_result:
                        files_created.append(tool_result["path"])

                # 检查工具失败
                if not tool_result.get("success"):
                    return StageResult(
                        stage=stage,
                        success=False,
                        message=tool_result.get("error", "工具执行失败"),
                    )

        return StageResult(
            stage=stage,
            success=True,
            message=f"阶段 {stage.value} 完成",
            files_created=files_created,
        )

    def _stress_test_stage(self, messages: List[Message]) -> StageResult:
        """运行带自愈的压力测试。"""
        # 获取 run_stress_test 工具
        stress_tool = self.tools["run_stress_test"]

        # 运行初始测试
        result = stress_tool.execute(trials=1000, n_max=100, t_max=3)

        retry_count = 0
        while not result["success"] and retry_count < self.max_retries:
            retry_count += 1
            self._log(f"对拍测试失败，第 {retry_count} 次尝试修正...")

            # 构建失败提示词
            failure_prompt = get_stress_test_failure_prompt(result, retry_count)
            messages.append(Message("user", failure_prompt))

            # 获取用于修复的 LLM 响应
            response = self.provider.chat(messages, tools=self._get_tool_definitions())

            # 执行工具调用（应该是 save_file）
            files_modified = []
            if "tool_calls" in response and response["tool_calls"]:
                for tool_call in response["tool_calls"]:
                    # 执行工具
                    tool_result = self._execute_tool(tool_call)

                    # 添加到对话
                    messages.append(Message("assistant", f"调用工具: {tool_call.name}"))
                    messages.append(Message("user", f"工具执行结果: {tool_result}"))

                    # 追踪修改的文件
                    if tool_result.get("success") and tool_call.name == "save_file":
                        if "path" in tool_result:
                            files_modified.append(tool_result["path"])

                            # 如果是 sol.cpp，重新编译
                            if tool_call.arguments.get("filename") == "sol.cpp":
                                compile_result = self.tools["compile_cpp"].execute("sol.cpp")
                                if not compile_result["success"]:
                                    return StageResult(
                                        stage=WorkflowStage.STRESS_TEST,
                                        success=False,
                                        message=f"编译失败: {compile_result.get('error')}",
                                    )

            # 重新运行压力测试
            result = stress_tool.execute(trials=1000, n_max=100, t_max=3)

        if result["success"]:
            return StageResult(
                stage=WorkflowStage.STRESS_TEST,
                success=True,
                message="压力测试通过",
                data={"trials": result.get("completed_rounds")},
            )
        else:
            return StageResult(
                stage=WorkflowStage.STRESS_TEST,
                success=False,
                message="自愈失败，已达到最大重试次数",
                data={"last_error": result},
            )

    def _package_stage(self, messages: List[Message]) -> StageResult:
        """将文件打包为 Polygon 格式。"""
        # 打包为 Polygon 格式
        pack_result = self.tools["pack_polygon_to_format"].execute()

        if not pack_result["success"]:
            return StageResult(
                stage=WorkflowStage.PACKAGE,
                success=False,
                message=pack_result.get("error", "打包失败"),
            )

        # 生成测试数据
        gen_result = self.tools["generate_tests"].execute(test_count=20)

        if not gen_result["success"]:
            return StageResult(
                stage=WorkflowStage.PACKAGE,
                success=False,
                message=f"测试数据生成失败: {gen_result.get('error')}",
            )

        return StageResult(
            stage=WorkflowStage.PACKAGE,
            success=True,
            message="打包完成",
            data=gen_result,
        )

    def _execute_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """执行工具调用。"""
        tool_name = tool_call.name
        arguments = tool_call.arguments

        if tool_name not in self.tools:
            return {"success": False, "error": f"找不到工具: {tool_name}"}

        try:
            tool = self.tools[tool_name]
            return tool.execute(**arguments)
        except Exception as e:
            return {"success": False, "error": f"工具执行错误: {str(e)}"}

    def _get_tool_definitions(self) -> List[Any]:
        """获取 LLM 的工具定义。"""
        from ..providers.base import ToolDefinition

        definitions = []
        for name, tool in self.tools.items():
            if hasattr(tool, "to_definition"):
                definitions.append(
                    ToolDefinition(
                        name=name,
                        description=tool.description,
                        parameters=tool.parameters,
                    )
                )

 )

        return definitions

    def _log(self, message: str) -> None:
        """如果启用了详细模式，记录消息。"""
        if self.verbose:
            print(f"[Agent] {message}")

    def get_status(self) -> Dict[str, Any]:
        """获取当前 Agent 状态。"""
        return {
            "progress": self.state.get_progress(),
            "current_stage": self.state.current_stage.value if self.state.current_stage else None,
            "completed_stages": [s.value for s in self.state.completed_stages],
            "work_dir": self.work_dir,
            "retry_count": self.state.retry_count,
            "files_created": self.state.files_created,
            "files_modified": self.state.files_modified,
        }
