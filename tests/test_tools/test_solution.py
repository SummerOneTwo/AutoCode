"""Solution 工具组测试（包含 Mixin 测试）。"""
import os
import tempfile

import pytest

from autocode_mcp.tools.mixins import BuildToolMixin, RunToolMixin
from autocode_mcp.tools.solution import SolutionBuildTool, SolutionRunTool
from autocode_mcp.utils.compiler import CompileResult, RunResult

# ============== Mixin 测试 ==============


class MockBuildTool(BuildToolMixin):
    """用于测试 BuildToolMixin 的 Mock 类。"""

    pass


class MockRunTool(RunToolMixin):
    """用于测试 RunToolMixin 的 Mock 类。"""

    pass


class MockCombinedTool(BuildToolMixin, RunToolMixin):
    """同时拥有 build 和 run 能力的 Mock 类。"""

    pass


class TestBuildToolMixin:
    """BuildToolMixin 测试。"""

    @pytest.mark.asyncio
    async def test_build_compiles_cpp_code(self, tmp_path):
        tool = MockBuildTool()

        source_path = tmp_path / "test.cpp"
        binary_path = tmp_path / "test.exe"

        source_path.write_text(
            '#include <iostream>\nint main() { std::cout << "hello"; return 0; }'
        )

        result = await tool.build(
            str(source_path),
            str(binary_path),
            compiler="g++",
            std="c++20",
            opt_level="O2",
            timeout=30,
        )

        assert isinstance(result, CompileResult)
        assert result.success
        assert result.binary_path == str(binary_path)
        assert os.path.exists(str(binary_path))

    @pytest.mark.asyncio
    async def test_build_returns_error_for_missing_source(self, tmp_path):
        tool = MockBuildTool()

        source_path = tmp_path / "nonexistent.cpp"
        binary_path = tmp_path / "test.exe"

        result = await tool.build(str(source_path), str(binary_path))

        assert isinstance(result, CompileResult)
        assert not result.success
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_build_returns_error_for_invalid_code(self, tmp_path):
        tool = MockBuildTool()

        source_path = tmp_path / "invalid.cpp"
        binary_path = tmp_path / "invalid.exe"

        source_path.write_text("this is not valid c++ code")

        result = await tool.build(str(source_path), str(binary_path))

        assert isinstance(result, CompileResult)
        assert not result.success
        assert result.error is not None


class TestRunToolMixin:
    """RunToolMixin 测试。"""

    @pytest.mark.asyncio
    async def test_run_uses_resource_limit_for_brute(self, tmp_path, monkeypatch):
        tool = MockCombinedTool()

        source_path = tmp_path / "brute.cpp"
        binary_path = tmp_path / "brute.exe"

        source_path.write_text(
            "#include <iostream>\nint main() { int x; std::cin >> x; std::cout << x * 2; return 0; }"
        )

        result = await tool.build(str(source_path), str(binary_path))
        assert result.success

        captured_limit = None

        import autocode_mcp.tools.mixins as mixins_module

        original_run_binary = mixins_module.run_binary

        async def mock_run_binary(binary_path, input_data, timeout, memory_mb):
            nonlocal captured_limit
            captured_limit = (timeout, memory_mb)
            return await original_run_binary(binary_path, input_data, timeout, memory_mb)

        monkeypatch.setattr(mixins_module, "run_binary", mock_run_binary)

        result = await tool.run(
            str(binary_path),
            "5\n",
            str(tmp_path),
            "brute",
        )

        assert captured_limit is not None
        assert captured_limit[0] == 60

    @pytest.mark.asyncio
    async def test_run_uses_resource_limit_for_sol(self, tmp_path, monkeypatch):
        tool = MockCombinedTool()

        source_path = tmp_path / "sol.cpp"
        binary_path = tmp_path / "sol.exe"

        source_path.write_text(
            "#include <iostream>\nint main() { int x; std::cin >> x; std::cout << x * 2; return 0; }"
        )

        result = await tool.build(str(source_path), str(binary_path))
        assert result.success

        captured_limit = None

        import autocode_mcp.tools.mixins as mixins_module

        original_run_binary = mixins_module.run_binary

        async def mock_run_binary(binary_path, input_data, timeout, memory_mb):
            nonlocal captured_limit
            captured_limit = (timeout, memory_mb)
            return await original_run_binary(binary_path, input_data, timeout, memory_mb)

        monkeypatch.setattr(mixins_module, "run_binary", mock_run_binary)

        result = await tool.run(
            str(binary_path),
            "5\n",
            str(tmp_path),
            "sol",
        )

        assert captured_limit is not None
        assert captured_limit[0] == 2

    @pytest.mark.asyncio
    async def test_run_accepts_custom_timeout_and_memory(self, tmp_path, monkeypatch):
        tool = MockCombinedTool()

        source_path = tmp_path / "sol.cpp"
        binary_path = tmp_path / "sol.exe"

        source_path.write_text(
            "#include <iostream>\nint main() { int x; std::cin >> x; std::cout << x * 2; return 0; }"
        )

        result = await tool.build(str(source_path), str(binary_path))
        assert result.success

        captured_limit = None

        import autocode_mcp.tools.mixins as mixins_module

        original_run_binary = mixins_module.run_binary

        async def mock_run_binary(binary_path, input_data, timeout, memory_mb):
            nonlocal captured_limit
            captured_limit = (timeout, memory_mb)
            return await original_run_binary(binary_path, input_data, timeout, memory_mb)

        monkeypatch.setattr(mixins_module, "run_binary", mock_run_binary)

        result = await tool.run(
            str(binary_path),
            "5\n",
            str(tmp_path),
            "sol",
            timeout=10,
            memory_mb=512,
        )

        assert captured_limit is not None
        assert captured_limit[0] == 10
        assert captured_limit[1] == 512

    @pytest.mark.asyncio
    async def test_run_returns_run_result(self, tmp_path):
        tool = MockCombinedTool()

        source_path = tmp_path / "test.cpp"
        binary_path = tmp_path / "test.exe"

        source_path.write_text(
            "#include <iostream>\nint main() { int x; std::cin >> x; std::cout << x * 2; return 0; }"
        )

        result = await tool.build(str(source_path), str(binary_path))
        assert result.success

        result = await tool.run(
            str(binary_path),
            "5\n",
            str(tmp_path),
            "sol",
        )

        assert isinstance(result, RunResult)
        assert result.success
        assert "10" in result.stdout


# ============== Solution 工具测试 ==============

SIMPLE_CPP = '''
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
'''

BRUTE_CPP = '''
#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    int sum = 0;
    for (int i = 1; i <= n; i++) {
        sum += i;
    }
    cout << sum << endl;
    return 0;
}
'''


@pytest.mark.asyncio
async def test_solution_build():
    """测试解法构建。"""
    tool = SolutionBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            code=SIMPLE_CPP,
        )

        assert result.success
        assert os.path.exists(result.data["source_path"])
        assert os.path.exists(result.data["binary_path"])


@pytest.mark.asyncio
async def test_solution_build_custom_name_keeps_standard_files(monkeypatch):
    """测试自定义命名构建时仍保留 sol.cpp/sol 可供默认流程使用。"""
    tool = SolutionBuildTool()

    async def fake_build(source_path, binary_path, compiler="g++", include_dirs=None):
        with open(binary_path, "w", encoding="utf-8") as f:
            f.write("binary")
        return CompileResult(success=True, binary_path=binary_path)

    monkeypatch.setattr(tool, "build", fake_build)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            name="accepted",
            code=SIMPLE_CPP,
        )

        assert result.success
        assert os.path.exists(os.path.join(tmpdir, "solutions", "accepted.cpp"))
        assert os.path.exists(os.path.join(tmpdir, "solutions", "sol.cpp"))
        assert os.path.exists(result.data["binary_path"])
        assert os.path.exists(result.data["standard_binary_path"])
        assert result.data["effective_name"] == "accepted"


@pytest.mark.asyncio
async def test_solution_build_brute():
    """测试暴力解法构建。"""
    tool = SolutionBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            solution_type="brute",
            code=BRUTE_CPP,
        )

        assert result.success
        assert os.path.exists(result.data["binary_path"])


@pytest.mark.asyncio
async def test_solution_build_invalid_code():
    """测试无效代码编译失败。"""
    tool = SolutionBuildTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            code="invalid c++ code {{{",
        )

        assert not result.success
        assert "compilation" in result.error.lower()


@pytest.mark.asyncio
async def test_solution_run():
    """测试解法运行。"""
    build_tool = SolutionBuildTool()
    run_tool = SolutionRunTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        build_result = await build_tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            code=SIMPLE_CPP,
        )
        assert build_result.success

        run_result = await run_tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            input_data="3 5\n",
        )

        assert run_result.success
        assert run_result.data["stdout"].strip() == "8"


@pytest.mark.asyncio
async def test_solution_run_not_found():
    """测试运行不存在的解法。"""
    tool = SolutionRunTool()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            input_data="test",
        )

        assert not result.success
        assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_solution_run_timeout():
    """测试运行超时。"""
    build_tool = SolutionBuildTool()
    run_tool = SolutionRunTool()

    infinite_loop = '''
#include <iostream>
using namespace std;
int main() {
    while(true) {}
    return 0;
}
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        build_result = await build_tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            code=infinite_loop,
        )
        assert build_result.success

        run_result = await run_tool.execute(
            problem_dir=tmpdir,
            solution_type="sol",
            input_data="",
            timeout=1,
        )

        assert not run_result.success
