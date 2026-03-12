"""
Prompt system for ACMGO Problem Setter Agent.

This package provides:
- System prompt
- Stage-specific prompts
- Few-shot examples
"""

from .system import SYSTEM_PROMPT, get_system_prompt
from .stages import (
    STAGE_STATEMENT_PROMPT,
    STAGE_SOLUTIONS_PROMPT,
    STAGE_VALIDATOR_PROMPT,
    STAGE_GENERATOR_PROMPT,
    STAGE_STRESS_TEST_PROMPT,
    STAGE_PACKAGE_PROMPT,
    get_stage_prompt,
    get_stress_test_failure_prompt,
)
from .examples import (
    EXAMPLE_STATEMENTS,
    EXAMPLE_SOLUTIONS,
    EXAMPLE_VALIDATOR,
    EXAMPLE_GENERATOR,
    get_example_statement,
    get_example_solution,
    get_all_example_types,
)

__all__ = [
    # System prompt
    "SYSTEM_PROMPT",
    "get_system_prompt",
    # Stage prompts
    "STAGE_STATEMENT_PROMPT",
    "STAGE_SOLUTIONS_PROMPT",
    "STAGE_VALIDATOR_PROMPT",
    "STAGE_GENERATOR_PROMPT",
    "STAGE_STRESS_TEST_PROMPT",
    "STAGE_PACKAGE_PROMPT",
    "get_stage_prompt",
    "get_stress_test_failure_prompt",
    # Examples
    "EXAMPLE_STATEMENTS",
    "EXAMPLE_SOLUTIONS",
    "EXAMPLE_VALIDATOR",
    "EXAMPLE_GENERATOR",
    "get_example_statement",
    "get_example_solution",
    "get_all_example_types",
]
