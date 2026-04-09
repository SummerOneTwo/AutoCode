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
            time_limit=2,  # 秒
            memory_limit=512,  # MB
        )

        assert result.success

        xml_path = os.path.join(problem_dir, "problem.xml")
        assert os.path.exists(xml_path)

        with open(xml_path) as f:
            content = f.read()
            assert "2000" in content  # time_limit_ms (2秒 * 1000)
            assert "536870912" in content  # memory_limit_bytes (512MB * 1024 * 1024)


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
async def test_problem_generate_tests_constraints_validation():
    """测试 constraints 参数验证。"""
    tool = ProblemGenerateTestsTool()

    # 测试 t_max 必须为正整数
    result = await tool.execute(
        problem_dir="/dummy",
        constraints={"t_max": 0},
    )
    assert not result.success
    assert "t_max must be positive" in result.error

    result = await tool.execute(
        problem_dir="/dummy",
        constraints={"t_max": -1},
    )
    assert not result.success
    assert "t_max must be positive" in result.error

    # 测试 sum_n_max 必须为正整数
    result = await tool.execute(
        problem_dir="/dummy",
        constraints={"sum_n_max": 0},
    )
    assert not result.success
    assert "sum_n_max must be positive" in result.error

    result = await tool.execute(
        problem_dir="/dummy",
        constraints={"sum_n_max": -5},
    )
    assert not result.success
    assert "sum_n_max must be positive" in result.error

    # 测试 n_max 不能大于 sum_n_max
    result = await tool.execute(
        problem_dir="/dummy",
        constraints={"n_max": 1000, "sum_n_max": 500},
    )
    assert not result.success
    assert "n_max cannot be greater than sum_n_max" in result.error

    # 测试 t_max 不能大于 sum_n_max
    result = await tool.execute(
        problem_dir="/dummy",
        constraints={"t_max": 100, "sum_n_max": 50},
    )
    assert not result.success
    assert "t_max cannot be greater than sum_n_max" in result.error

    # 测试有效的 constraints 应该通过验证（会因缺少 generator 而失败，但不是验证失败）
    result = await tool.execute(
        problem_dir="/nonexistent",
        constraints={"n_max": 1000, "t_max": 10, "sum_n_max": 10000},
    )
    assert not result.success
    assert "Generator not found" in result.error  # 验证通过，但找不到 generator


@pytest.mark.asyncio
async def test_problem_generate_tests_test_configs_validation():
    """测试 test_configs 参数验证。"""
    tool = ProblemGenerateTestsTool()

    # 测试缺少 type 字段
    result = await tool.execute(
        problem_dir="/dummy",
        test_configs=[{"n_min": 1, "n_max": 10, "t_min": 1, "t_max": 5}],
    )
    assert not result.success
    assert "test_configs[0]: 'type' is required" in result.error

    # 测试 type 字段值无效
    result = await tool.execute(
        problem_dir="/dummy",
        test_configs=[{"type": "5", "n_min": 1, "n_max": 10, "t_min": 1, "t_max": 5}],
    )
    assert not result.success
    assert "test_configs[0]: 'type' must be one of '1', '2', '3', '4'" in result.error

    # 测试缺少必需字段
    result = await tool.execute(
        problem_dir="/dummy",
        test_configs=[{"type": "1", "n_min": 1, "n_max": 10, "t_min": 1}],  # 缺少 t_max
    )
    assert not result.success
    assert "test_configs[0]: 't_max' is required" in result.error

    # 测试字段值为负数
    result = await tool.execute(
        problem_dir="/dummy",
        test_configs=[{"type": "1", "n_min": -1, "n_max": 10, "t_min": 1, "t_max": 5}],
    )
    assert not result.success
    assert "test_configs[0]: 'n_min' must be a non-negative integer" in result.error

    # 测试 n_min > n_max
    result = await tool.execute(
        problem_dir="/dummy",
        test_configs=[{"type": "1", "n_min": 100, "n_max": 10, "t_min": 1, "t_max": 5}],
    )
    assert not result.success
    assert "test_configs[0]: n_min cannot be greater than n_max" in result.error

    # 测试 t_min > t_max
    result = await tool.execute(
        problem_dir="/dummy",
        test_configs=[{"type": "1", "n_min": 1, "n_max": 10, "t_min": 10, "t_max": 5}],
    )
    assert not result.success
    assert "test_configs[0]: t_min cannot be greater than t_max" in result.error

    # 测试有效的 test_configs 应该通过验证（会因缺少 generator 而失败）
    result = await tool.execute(
        problem_dir="/nonexistent",
        test_configs=[{"type": "1", "n_min": 1, "n_max": 10, "t_min": 1, "t_max": 5}],
    )
    assert not result.success
    assert "Generator not found" in result.error  # 验证通过，但找不到 generator


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


@pytest.mark.asyncio
async def test_problem_generate_tests_dedup():
    """测试去重功能。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    create_tool = ProblemCreateTool()
    gen_tool = GeneratorBuildTool()
    sol_tool = SolutionBuildTool()
    generate_tool = ProblemGenerateTestsTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "dedup_test")
        await create_tool.execute(problem_dir=problem_dir, problem_name="Dedup Test")

        # Generator 固定输出相同内容（用于测试去重）
        fixed_gen = """
#include "testlib.h"
#include <iostream>
int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    std::cout << "1 2" << std::endl;  // 固定输出
    return 0;
}
"""
        simple_sol = """
#include <iostream>
int main() {
    int a, b;
    std::cin >> a >> b;
    std::cout << a + b << std::endl;
    return 0;
}
"""
        await gen_tool.execute(problem_dir=problem_dir, code=fixed_gen)
        await sol_tool.execute(problem_dir=problem_dir, solution_type="sol", code=simple_sol)

        # 启用去重，请求 10 个测试但 generator 只能产生 1 种输出
        result = await generate_tool.execute(
            problem_dir=problem_dir,
            test_count=10,
            enable_dedup=True,
            oversample_ratio=2.0,  # 尝试生成 20 个候选
        )

        # 由于去重，实际生成的测试应该少于请求的数量
        # 因为 generator 只能产生 1 种输出，最终只有 1 个测试
        # 这是一个 partial generation 失败
        assert not result.success
        assert "Partial generation" in result.error
        # 验证只生成了 1 个测试（去重生效）
        assert len(result.data.get("generated_tests", [])) == 1


@pytest.mark.asyncio
async def test_problem_generate_tests_balance():
    """测试平衡分布功能。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    create_tool = ProblemCreateTool()
    gen_tool = GeneratorBuildTool()
    sol_tool = SolutionBuildTool()
    generate_tool = ProblemGenerateTestsTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "balance_test")
        await create_tool.execute(problem_dir=problem_dir, problem_name="Balance Test")

        # Generator 根据类型输出不同标记
        type_aware_gen = """
#include "testlib.h"
#include <iostream>
int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    int type = atoi(argv[2]);
    std::cout << "type" << type << " " << rnd.next(1, 100) << std::endl;
    return 0;
}
"""
        simple_sol = """
#include <iostream>
int main() {
    std::string s;
    int n;
    std::cin >> s >> n;
    std::cout << s << " " << n << std::endl;
    return 0;
}
"""
        await gen_tool.execute(problem_dir=problem_dir, code=type_aware_gen)
        await sol_tool.execute(problem_dir=problem_dir, solution_type="sol", code=simple_sol)

        # 使用多种类型的配置
        custom_configs = [
            {"type": "1", "n_min": 1, "n_max": 10, "t_min": 1, "t_max": 1},  # tiny
            {"type": "2", "n_min": 1, "n_max": 10, "t_min": 1, "t_max": 1},  # random
            {"type": "3", "n_min": 1, "n_max": 10, "t_min": 1, "t_max": 1},  # extreme
            {"type": "4", "n_min": 1, "n_max": 10, "t_min": 1, "t_max": 1},  # tle
        ]

        result = await generate_tool.execute(
            problem_dir=problem_dir,
            test_count=8,
            test_configs=custom_configs,
            enable_balance=True,
            oversample_ratio=2.0,
        )

        assert result.success
        assert result.data.get("balance_enabled") is True
        # 检查类型分布
        type_dist = result.data.get("type_distribution", {})
        # 应该有 4 种类型，每种 2 个
        assert len(type_dist) == 4


@pytest.mark.asyncio
async def test_problem_generate_tests_oversample():
    """测试超额采样功能。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    create_tool = ProblemCreateTool()
    gen_tool = GeneratorBuildTool()
    sol_tool = SolutionBuildTool()
    generate_tool = ProblemGenerateTestsTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        problem_dir = os.path.join(tmpdir, "oversample_test")
        await create_tool.execute(problem_dir=problem_dir, problem_name="Oversample Test")

        simple_gen = """
#include "testlib.h"
#include <iostream>
int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    int seed = atoi(argv[1]);
    rnd.setSeed(seed);
    std::cout << rnd.next(1, 1000) << std::endl;
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

        result = await generate_tool.execute(
            problem_dir=problem_dir,
            test_count=10,
            oversample_ratio=2.0,  # 生成 20 个候选
        )

        assert result.success
        # 检查候选数量
        candidates = result.data.get("candidates_generated", 0)
        assert candidates >= 10  # 至少生成了 10 个候选
        assert "from" in result.data.get("message", "")  # 消息中应该包含候选数量
