"""
Problem 工具组测试。
"""

import os
import tempfile

import pytest

from autocode_mcp.tools.generator import GeneratorBuildTool
from autocode_mcp.tools.problem import (
    ProblemCreateTool,
    ProblemGenerateTestsTool,
    ProblemPackPolygonTool,
)
from autocode_mcp.tools.solution import SolutionBuildTool


@pytest.mark.asyncio
async def test_problem_create():
    """测试题目目录创建。"""
    tool = ProblemCreateTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "test_problem")
        result = await tool.execute(
            problem_dir=problem_dir,
            problem_name="Test Problem",
        )

        assert result.success
        assert os.path.exists(problem_dir)
        assert os.path.exists(os.path.join(problem_dir, "files"))
        assert os.path.exists(os.path.join(problem_dir, "solutions"))
        assert os.path.exists(os.path.join(problem_dir, "statements"))
        assert os.path.exists(os.path.join(problem_dir, "tests"))


@pytest.mark.asyncio
async def test_problem_create_readme():
    """测试题目 README 创建。"""
    tool = ProblemCreateTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "readme_test")
        await tool.execute(
            problem_dir=problem_dir,
            problem_name="README Test",
        )

        readme_path = os.path.join(problem_dir, "statements", "README.md")
        assert os.path.exists(readme_path)

        with open(readme_path, encoding="utf-8") as f:
            content = f.read()
            assert "README Test" in content


@pytest.mark.asyncio
async def test_problem_pack_polygon():
    """测试 Polygon 打包。"""
    create_tool = ProblemCreateTool()
    pack_tool = ProblemPackPolygonTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "pack_test")

        # 创建目录
        await create_tool.execute(
            problem_dir=problem_dir,
            problem_name="Pack Test",
        )

        # 创建一些测试文件
        with open(os.path.join(problem_dir, "sol.cpp"), "w") as f:
            f.write("// sol.cpp")
        with open(os.path.join(problem_dir, "brute.cpp"), "w") as f:
            f.write("// brute.cpp")

        # 打包
        result = await pack_tool.execute(problem_dir=problem_dir)

        assert result.success
        assert os.path.exists(os.path.join(problem_dir, "problem.xml"))


@pytest.mark.asyncio
async def test_problem_pack_polygon_creates_xml():
    """测试 Polygon 打包生成 problem.xml。"""
    tool = ProblemPackPolygonTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "xml_test")
        os.makedirs(problem_dir)

        result = await tool.execute(
            problem_dir=problem_dir,
            time_limit=2000,
            memory_limit=536870912,
        )

        assert result.success

        xml_path = os.path.join(problem_dir, "problem.xml")
        assert os.path.exists(xml_path)

        with open(xml_path) as f:
            content = f.read()
            assert "2000" in content  # time_limit
            assert "536870912" in content  # memory_limit


@pytest.mark.asyncio
async def test_problem_generate_tests_custom_configs():
    """测试使用自定义 test_configs 生成测试数据。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    create_tool = ProblemCreateTool()
    gen_tool = GeneratorBuildTool()
    sol_tool = SolutionBuildTool()
    generate_tool = ProblemGenerateTestsTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "custom_config_test")
        await create_tool.execute(problem_dir=problem_dir, problem_name="Custom Config")

        # 简单的 generator 和 solution
        simple_gen = """
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
        simple_sol = """
#include <iostream>
int main() {
    int n;
    std::cin >> n;
    std::cout << n << std::endl;
    return 0;
}
"""
        await gen_tool.execute(problem_dir=problem_dir, code=simple_gen)
        await sol_tool.execute(problem_dir=problem_dir, solution_type="sol", code=simple_sol)

        # 使用自定义配置
        custom_configs = [
            {"type": "1", "n_min": 1, "n_max": 5, "t_min": 1, "t_max": 1, "seed_offset": 0},
            {"type": "2", "n_min": 10, "n_max": 20, "t_min": 1, "t_max": 1, "seed_offset": 0},
        ]

        result = await generate_tool.execute(
            problem_dir=problem_dir,
            test_count=2,
            test_configs=custom_configs,
        )

        assert result.success
        assert len(result.data["generated_tests"]) == 2


@pytest.mark.asyncio
async def test_problem_pack_polygon_dynamic_test_count():
    """测试 Polygon 打包使用动态 test-count。"""
    create_tool = ProblemCreateTool()
    pack_tool = ProblemPackPolygonTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "dynamic_test_count_test")
        await create_tool.execute(problem_dir=problem_dir, problem_name="Dynamic Test")

        # 创建 tests 目录和 5 个测试文件
        tests_dir = os.path.join(problem_dir, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        for i in range(1, 6):
            with open(os.path.join(tests_dir, f"{i:02d}.in"), "w") as f:
                f.write(f"test {i}\n")
            with open(os.path.join(tests_dir, f"{i:02d}.ans"), "w") as f:
                f.write(f"answer {i}\n")

        await pack_tool.execute(problem_dir=problem_dir)

        xml_path = os.path.join(problem_dir, "problem.xml")
        with open(xml_path, encoding="utf-8") as f:
            content = f.read()
            assert "<test-count>5</test-count>" in content
            assert "<test-count>20</test-count>" not in content
