"""Stress Test 集成测试。"""

import tempfile

import pytest

from autocode_mcp.tools.generator import GeneratorBuildTool
from autocode_mcp.tools.solution import SolutionBuildTool
from autocode_mcp.tools.stress_test import StressTestRunTool

# 基于 seed 输出不同数据的 generator
SEED_BASED_GENERATOR = """
#include "testlib.h"
#include <iostream>

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    int seed = atoi(argv[1]);
    rnd.setSeed(seed);

    int a = rnd.next(1, 100);
    int b = rnd.next(1, 100);

    std::cout << a << " " << b << std::endl;

    return 0;
}
"""

SIMPLE_ADDITION_SOL = """
#include <iostream>

int main() {
    int a, b;
    std::cin >> a >> b;
    std::cout << a + b << std::endl;
    return 0;
}
"""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stress_test_generates_different_inputs_per_round():
    """验证每轮对拍使用不同 seed 生成不同输入数据。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    tool = StressTestRunTool()
    build_tool = SolutionBuildTool()
    gen_tool = GeneratorBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        await gen_tool.execute(problem_dir=tmpdir, code=SEED_BASED_GENERATOR)
        await build_tool.execute(problem_dir=tmpdir, solution_type="sol", code=SIMPLE_ADDITION_SOL)
        await build_tool.execute(
            problem_dir=tmpdir, solution_type="brute", code=SIMPLE_ADDITION_SOL
        )

        result = await tool.execute(problem_dir=tmpdir, trials=10)

        assert result.success
        assert result.data["completed_rounds"] == 10
