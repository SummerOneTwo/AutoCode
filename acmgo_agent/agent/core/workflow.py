"""
Workflow orchestrator for managing the 6-step problem setting process.
"""
from typing import List, Dict, Any, Optional, Callable
from .state import WorkflowStage, StageResult


class WorkflowOrchestrator:
    """
    Orchestrates the 6-step problem setting workflow.

    This class provides a higher-level interface for managing
    the workflow with hooks and stage transitions.
    """

    def __init__(self):
        """Initialize workflow orchestrator."""
        self.current_stage: Optional[WorkflowStage] = None
        self.completed_stages: List[WorkflowStage] = []
        self.stage_results: Dict[WorkflowStage, StageResult] = {}

        # Stage hooks
        self.before_stage_hooks: Dict[WorkflowStage, List[Callable]] = {}
        self.after_stage_hooks: Dict[WorkflowStage, List[Callable]] = {}

        # Global hooks
        self.before_any_stage: List[Callable] = []
        self.after_any_stage: List[Callable] = []

    def register_before_stage_hook(
        self, stage: WorkflowStage, hook: Callable
    ) -> None:
        """Register a hook to run before a specific stage."""
        if stage not in self.before_stage_hooks:
            self.before_stage_hooks[stage] = []
        self.before_stage_hooks[stage].append(hook)

    def register_after_stage_hook(
        self, stage: WorkflowStage, hook: Callable
    ) -> None:
        """Register a hook to run after a specific stage."""
        if stage not in self.after_stage_hooks:
            self.after_stage_hooks[stage] = []
        self.after_stage_hooks[stage].append(hook)

    def register_before_any_stage_hook(self, hook: Callable) -> None:
        """Register a hook to run before any stage."""
        self.before_any_stage.append(hook)

    def register_after_any_stage_hook(self, hook: Callable) -> None:
        """Register a hook to run after any stage."""
        self.after_any_stage.append(hook)

    def get_stage_order(self) -> List[WorkflowStage]:
        """Get the default order of stages."""
        return [
            WorkflowStage.STATEMENT,
            WorkflowStage.SOLUTIONS,
            WorkflowStage.VALIDATOR,
            WorkflowStage.GENERATOR,
            WorkflowStage.STRESS_TEST,
            WorkflowStage.PACKAGE,
        ]

    def get_next_stage(self) -> Optional[WorkflowStage]:
        """Get the next stage in the workflow."""
        if self.current_stage is None:
            return self.get_stage_order()[0]

        stages = self.get_stage_order()
        try:
            idx = stages.index(self.current_stage)
            if idx + 1 < len(stages):
                return stages[idx + 1]
        except ValueError:
            pass

        return None

    def get_previous_stage(self) -> Optional[WorkflowStage]:
        """Get the previous stage in the workflow."""
        if self.current_stage is None:
            return None

        stages = self.get_stage_order()
        try:
            idx = stages.index(self.current_stage)
            if idx > 0:
                return stages[idx - 1]
        except ValueError:
            pass

        return None

    def get_remaining_stages(self) -> List[WorkflowStage]:
        """Get list of stages not yet completed."""
        all_stages = self.get_stage_order()
        return [s for s in all_stages if s not in self.completed_stages]

    def can_proceed_to_stage(self, stage: WorkflowStage) -> bool:
        """
        Check if a stage can be started.

        A stage can be started if all previous stages are completed.
        """
        stages = self.get_stage_order()
        stage_index = stages.index(stage)

        for i in range(stage_index):
            if stages[i] not in self.completed_stages:
                return False

        return True

    def get_stage_dependencies(self, stage: WorkflowStage) -> List[WorkflowStage]:
        """Get list of stages that must be completed before this stage."""
        stages = self.get_stage_order()
        stage_index = stages.index(stage)
        return stages[:stage_index]

    def execute_before_stage_hooks(
        self, stage: WorkflowStage, context: Dict[str, Any]
    ) -> None:
        """Execute all before-stage hooks for the given stage."""
        # Global hooks
        for hook in self.before_any_stage:
            hook(stage.value, context)

        # Stage-specific hooks
        if stage in self.before_stage_hooks:
            for hook in self.before_stage_hooks[stage]:
                hook(context)

    def execute_after_stage_hooks(
        self, stage: WorkflowStage, result: StageResult, context: Dict[str, Any]
    ) -> None:
        """Execute all after-stage hooks for the given stage."""
        # Stage-specific hooks
        if stage in self.after_stage_hooks:
            for hook in self.after_stage_hooks[stage]:
                hook(result, context)

        # Global hooks
        for hook in self.after_any_stage:
            hook(stage.value, result.__dict__, context)

    def complete_stage(self, stage: WorkflowStage, result: StageResult) -> None:
        """Mark a stage as complete with its result."""
        self.stage_results[stage] = result
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.current_stage = stage

    def is_complete(self) -> bool:
        """Check if all stages are completed."""
        return len(self.completed_stages) == len(self.get_stage_order())

    def reset(self) -> None:
        """Reset the workflow to initial state."""
        self.current_stage = None
        self.completed_stages = []
        self.stage_results = {}

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow status."""
        all_stages = self.get_stage_order()
        completed_count = len(self.completed_stages)

        return {
            "total_stages": len(all_stages),
            "completed_stages": completed_count,
            "progress_percentage": (completed_count / len(all_stages)) * 100,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "completed_stage_names": [s.value for s in self.completed_stages],
            "remaining_stages": [s.value for s in self.get_remaining_stages()],
        }
