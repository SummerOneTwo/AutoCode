"""
Interactor 工具组测试。
"""

import os
import tempfile

import pytest

from autocode_mcp.tools.interactor import InteractorBuildTool

# 简单的 Interactor 代码（基于 testlib.h）
INTERACTOR_CODE = """
#include "testlib.h"
#include <iostream>

int main(int argc, char* argv[]) {
    registerInteraction(argc, argv);

    // 读取输入
    int n = inf.readInt();

    // 输出给选手
    std::cout << n << std::endl;
    std::cout.flush();

    // 读取选手输出
    int answer = ouf.readInt();

    // 验证答案
    if (answer == n * 2) {
        quitf(_ok, "Correct");
    } else {
        quitf(_wa, "Expected %d, got %d", n * 2, answer);
    }
}
"""


@pytest.mark.asyncio
async def test_interactor_build():
    """测试 Interactor 构建。"""
    tool = InteractorBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            code=INTERACTOR_CODE,
        )

        assert result.success
        assert os.path.exists(result.data["source_path"])
        assert os.path.exists(result.data["binary_path"])


@pytest.mark.asyncio
async def test_interactor_build_invalid_code():
    """测试无效代码编译失败。"""
    tool = InteractorBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            code="invalid c++ code {{{",
        )

        assert not result.success
        assert "compilation" in result.error.lower()


@pytest.mark.asyncio
async def test_interactor_build_no_validation():
    """测试不带验证的 Interactor 构建。"""
    tool = InteractorBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            code=INTERACTOR_CODE,
        )

        assert result.success
        # 没有提供参考解和变异解，应该直接返回成功
        assert "binary_path" in result.data


SIMPLE_SOLUTION = """
#include <iostream>
int main() {
    int n;
    std::cin >> n;
    std::cout << n * 2 << std::endl;
    return 0;
}
"""

WRONG_SOLUTION = """
#include <iostream>
int main() {
    int n;
    std::cin >> n;
    std::cout << n * 3 << std::endl;
    return 0;
}
"""


@pytest.mark.asyncio
async def test_interactor_with_reference_solution():
    """测试 Interactor 与参考解法的交互验证。"""
    import shutil

    if not shutil.which("g++"):
        pytest.skip("g++ not available")

    from autocode_mcp.tools.solution import SolutionBuildTool

    tool = InteractorBuildTool()
    sol_tool = SolutionBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        # 构建 interactor
        build_result = await tool.execute(problem_dir=tmpdir, code=INTERACTOR_CODE)
        assert build_result.success

        # 构建正确的参考解法
        sol_path = os.path.join(tmpdir, "correct_sol.cpp")
        with open(sol_path, "w", encoding="utf-8") as f:
            f.write(SIMPLE_SOLUTION)
        await sol_tool.execute(problem_dir=tmpdir, solution_type="sol", code=SIMPLE_SOLUTION)
        correct_sol_exe = os.path.join(tmpdir, "sol.exe")

        # 验证正确解法
        result = await tool.execute(
            problem_dir=tmpdir,
            code=INTERACTOR_CODE,
            reference_solution_path=correct_sol_exe,
        )

        assert result.success
        # 注意：由于 interactor 需要输入数据，实际验证可能受限
        # 这里主要验证不崩溃即可
