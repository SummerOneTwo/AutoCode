"""
Core agent implementation for ACMGO Problem Setter.

This package provides:
- Agent state management
- Workflow orchestration
- Main problem setter agent
"""

from .state import (
    WorkflowStage,
    StageResult,
    AgentState,
)
from .workflow import WorkflowOrchestrator
from .agent import ProblemSetterAgent

__all__ = [
    "WorkflowStage",
    "StageResult",
    "AgentState",
    "WorkflowOrchestrator",
    "ProblemSetterAgent",
]
