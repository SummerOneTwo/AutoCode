"""题目工作流集成测试。"""

import os
import tempfile

import pytest

from autocode_mcp.tools.generator import GeneratorBuildTool
from autocode_mcp.tools.problem import (
    ProblemCreateTool,
    ProblemGenerateTestsTool,
)
from autocode_mcp.tools.solution import SolutionBuildTool

SIMPLE_GEN = """
#include "testlib.h"
#include <iostream>
int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    int seed = atoi(argv[1]);
    int type = atoi(argv[2]);
    int n_min = atoi(argv[3]);
    int n_max = atoi(argv[4]);
    rnd.setSeed(seed);
    int n = rnd.next(n_min, n_max);
    std::cout << n << std::endl;
    return 0;
}
"""

SIMPLE_SOL = """
#include <iostream>
int main() {
    int n;
    std::cin >> n;
    std::cout << n << std::endl;
    return 0;
}
"""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_problem_workflow():
    """测试完整的题目创建到测试生成流程。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "integration_test")

        # 1. 创建题目
        create_tool = ProblemCreateTool()
        create_result = await create_tool.execute(
            problem_dir=problem_dir,
            problem_name="Integration Test",
        )
        assert create_result.success

        # 2. 构建 generator 和 solution
        gen_tool = GeneratorBuildTool()
        sol_tool = SolutionBuildTool()

        await gen_tool.execute(problem_dir=problem_dir, code=SIMPLE_GEN)
        await sol_tool.execute(problem_dir=problem_dir, solution_type="sol", code=SIMPLE_SOL)

        # 3. 生成测试数据
        generate_tool = ProblemGenerateTestsTool()
        generate_result = await generate_tool.execute(
            problem_dir=problem_dir,
            test_count=3,
        )

        assert generate_result.success
        assert len(generate_result.data["generated_tests"]) >= 1

        # 4. 验证测试文件存在
        tests_dir = os.path.join(problem_dir, "tests")
        assert os.path.exists(tests_dir)
        test_files = [f for f in os.listdir(tests_dir) if f.endswith(".in")]
        assert len(test_files) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_problem_generate_tests_with_custom_configs():
    """测试使用自定义配置生成测试数据。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "custom_config_integration")

        create_tool = ProblemCreateTool()
        await create_tool.execute(problem_dir=problem_dir, problem_name="Custom Config")

        gen_tool = GeneratorBuildTool()
        sol_tool = SolutionBuildTool()

        await gen_tool.execute(problem_dir=problem_dir, code=SIMPLE_GEN)
        await sol_tool.execute(problem_dir=problem_dir, solution_type="sol", code=SIMPLE_SOL)

        custom_configs = [
            {"type": "1", "n_min": 1, "n_max": 5, "t_min": 1, "t_max": 1, "seed_offset": 0},
            {"type": "2", "n_min": 10, "n_max": 20, "t_min": 1, "t_max": 1, "seed_offset": 0},
            {"type": "3", "n_min": 50, "n_max": 100, "t_min": 1, "t_max": 1, "seed_offset": 0},
        ]

        generate_tool = ProblemGenerateTestsTool()
        result = await generate_tool.execute(
            problem_dir=problem_dir,
            test_count=3,
            test_configs=custom_configs,
        )

        assert result.success
        assert len(result.data["generated_tests"]) >= 1
