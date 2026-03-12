"""
用于追踪工作流程进度的 Agent 状态管理。
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class WorkflowStage(Enum):
    """出题工作流程的 6 个阶段。"""
    STATEMENT = "statement"  # 步骤 1：设计题面
    SOLUTIONS = "solutions"  # 步骤 2：实现 sol.cpp 和 brute.cpp
    VALIDATOR = "validator"  # 步骤 3：实现 val.cpp
    GENERATOR = "generator"  # 步骤 4：实现 gen.cpp
    STRESS_TEST = "stress_test"  # 步骤 5：运行压力测试
    PACKAGE = "package"  # 步骤 6：打包为 Polygon 格式

    @classmethod
    def from_string(cls, value: str) -> "WorkflowStage":
        """将字符串转换为 WorkflowStage。"""
        for stage in cls:
            if stage.value == value:
                return stage
        raise ValueError(f"未知的工作流程阶段: {value}")

    @property
    def display_name(self) -> str:
        """获取阶段的显示名称。"""
        names = {
            WorkflowStage.STATEMENT: "题面设计 (Statement)",
            WorkflowStage.SOLUTIONS: "双解法实现 (Dual Solutions)",
            WorkflowStage.VALIDATOR: "数据校验器 (Validator)",
            WorkflowStage.GENERATOR: "数据生成器 (Generator)",
            WorkflowStage.STRESS_TEST: "自动化对拍 (Stress Test)",
            WorkflowStage.PACKAGE: "最终打包 (Final Package)",
        }
        return names[self]

    @property
    def next_stage(self) -> Optional["WorkflowStage"]:
        """获取下一阶段，如果是最后一个阶段则返回 None。"""
        stages = list(WorkflowStage)
        idx = stages.index(self)
        if idx < len(stages) - 1:
            return stages[idx + 1]
        return None


@dataclass
class StageResult:
    """工作流程阶段完成的结果。"""
    stage: WorkflowStage
    success: bool
    message: str
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """
    在工作流程执行期间追踪 Agent 的状态。

    包括：
    - 当前工作流程阶段
    - 已完成的阶段及其结果
    - 题目元数据（名称、描述、约束）
    - 已创建/修改的文件
    - 错误状态和恢复尝试
    """

    # 工作流程追踪
    current_stage: Optional[WorkflowStage] = None
    completed_stages: List[WorkflowStage] = field(default_factory=list)
    stage_results: Dict[WorkflowStage, StageResult] = field(default_factory=dict)

    # 题目元数据
    problem_name: str = ""
    problem_description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)

    # 文件追踪
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)

    # 错误和恢复追踪
    last_error: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3

    # 对话状态
    conversation_messages: List[Dict[str, str]] = field(default_factory=list)

    def is_complete(self) -> bool:
        """检查是否所有阶段都已完成。"""
        return len(self.completed_stages) == len(WorkflowStage)

    def is_stage_completed(self, stage: WorkflowStage) -> bool:
        """检查特定阶段是否已完成。"""
        return stage in self.completed_stages

    def mark_stage_complete(
        self,
        stage: WorkflowStage,
        result: StageResult
    ) -> None:
        """将阶段标记为已完成并记录结果。"""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.stage_results[stage] = result
        self.current_stage = stage.next_stage

        # 更新文件追踪
        self.files_created.extend(result.files_created)
        self.files_modified.extend(result.files_modified)

    def set_current_stage(self, stage: WorkflowStage) -> None:
        """设置当前阶段。"""
        self.current_stage = stage



    def add_error(self, error: Dict[str, Any]) -> None:
        """记录错误并增加重试次数。"""
        self.last_error = error
        self.retry_count += 1

    def reset_retry_count(self) -> None:
        """重置重试次数（成功恢复后）。"""
        self.retry_count = 0
        self.last_error = None

    def can_retry(self) -> bool:
        """检查是否还有重试机会。"""
        return self.retry_count < self.max_retries

    def add_message(self, role: str, content: str) -> None:
        """向对话历史添加消息。"""
        self.conversation_messages.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        """获取所有对话消息。"""
        return self.conversation_messages.copy()

    def clear_messages(self) -> None:
        """清除所有对话消息。"""
        self.conversation_messages.clear()

    def get_progress(self) -> float:
        """以百分比形式获取进度（0-100）。"""
        total = len(WorkflowStage)
        completed = len(self.completed_stages)
        return (completed / total) * 100

    def get_status_summary(self) -> str:
        """获取人类可读的状态摘要。"""
        status = []

        # 进度
        status.append(f"进度: {self.get_progress():.1f}%")

        # 当前阶段
        if self.current_stage:
            status.append(f"当前阶段: {self.current_stage.display_name}")
        elif self.is_complete():
            status.append("状态: 完成")
        else:
            status.append("状态: 未开始")

        # 错误状态
        if self.last_error:
            status.append(f"重试: {self.retry_count}/{self.max_retries}")

        return " | ".join(status)
