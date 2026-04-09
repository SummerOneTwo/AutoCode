"""测试打包配置和模板访问。"""
import os

import pytest


def test_templates_in_package():
    """测试模板文件在包内可访问。"""
    from autocode_mcp import TEMPLATES_DIR

    assert os.path.exists(TEMPLATES_DIR), f"TEMPLATES_DIR not found: {TEMPLATES_DIR}"
    assert os.path.exists(os.path.join(TEMPLATES_DIR, "testlib.h"))


def test_resources_module_templates():
    """测试 resources 模块可以访问模板。"""
    from autocode_mcp.resources import get_template_path, list_templates

    templates = list_templates()
    assert "testlib.h" in templates

    path = get_template_path("testlib.h")
    assert path is not None
    assert os.path.exists(path)


@pytest.mark.asyncio
async def test_mcp_call_tool_result_type():
    """测试 call_tool 返回正确的 MCP 类型。"""
    from mcp.types import CallToolResult

    from autocode_mcp.server import call_tool, register_all_tools

    # 注册工具
    register_all_tools()

    # 测试未知工具
    result = await call_tool("unknown_tool", {})
    assert isinstance(result, CallToolResult)
    assert result.isError is True


@pytest.mark.asyncio
async def test_mcp_call_tool_success_result():
    """测试 call_tool 成功时返回正确的结果。"""
    from mcp.types import CallToolResult

    from autocode_mcp.server import call_tool, register_all_tools

    # 注册工具
    register_all_tools()

    # 使用临时目录测试 file_read
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个测试文件
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        result = await call_tool("file_read", {"path": test_file})
        assert isinstance(result, CallToolResult)
        assert result.isError is False
        assert result.structuredContent is not None


@pytest.mark.asyncio
async def test_mcp_get_prompt_result_type():
    """测试 get_prompt 返回正确的 MCP 类型。"""
    from mcp.types import GetPromptResult

    from autocode_mcp.server import get_prompt

    # 测试存在的 prompt
    result = await get_prompt("validator")
    assert isinstance(result, GetPromptResult)
    assert len(result.messages) > 0

    # 测试不存在的 prompt
    result = await get_prompt("nonexistent_prompt")
    assert isinstance(result, GetPromptResult)
    assert "not found" in result.description.lower() or "error" in result.description.lower()


@pytest.mark.asyncio
async def test_mcp_read_resource_result_type():
    """测试 read_resource 返回正确的 MCP 类型。"""
    from mcp.types import ReadResourceResult

    from autocode_mcp.server import read_resource

    # 测试模板资源
    result = await read_resource("template://testlib.h")
    assert isinstance(result, ReadResourceResult)
    assert len(result.contents) > 0
    assert result.contents[0].text is not None

    # 测试不存在的模板
    result = await read_resource("template://nonexistent.txt")
    assert isinstance(result, ReadResourceResult)
    assert "not found" in result.contents[0].text.lower()


def test_all_template_files_exist():
    """测试所有模板文件都存在。"""
    from autocode_mcp import TEMPLATES_DIR

    expected_templates = [
        "testlib.h",
        "validator_template.cpp",
        "generator_template.cpp",
        "checker_template.cpp",
        "interactor_template.cpp",
    ]

    for template in expected_templates:
        path = os.path.join(TEMPLATES_DIR, template)
        assert os.path.exists(path), f"Template not found: {template}"


@pytest.mark.asyncio
async def test_interactor_reference_solution_not_found():
    """测试 interactor_build 在参考解不存在时报错而非静默跳过。"""
    from autocode_mcp.server import call_tool, register_all_tools

    register_all_tools()

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 测试不存在的参考解路径
        result = await call_tool("interactor_build", {
            "problem_dir": tmpdir,
            "code": '#include "testlib.h"\nint main() { return 0; }',
            "reference_solution_path": os.path.join(tmpdir, "nonexistent.exe"),
        })

        assert result.isError is True
        assert "Reference solution not found" in result.structuredContent.get("error", "")


@pytest.mark.asyncio
async def test_interactor_pass_rate_without_tests():
    """测试 interactor_build 没有测试时 pass_rate 为 0 而非 1.0。"""
    from autocode_mcp.server import call_tool, register_all_tools

    register_all_tools()

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 不提供参考解和变异解
        result = await call_tool("interactor_build", {
            "problem_dir": tmpdir,
            "code": '#include "testlib.h"\nint main() { return 0; }',
        })

        assert result.isError is False
        # pass_rate 在 data 字段中
        data = result.structuredContent.get("data", {})
        assert data.get("pass_rate", 1.0) == 0.0


@pytest.mark.asyncio
async def test_checker_fail_verdict():
    """测试 checker_build 能区分 FAIL 和 WA。"""
    from autocode_mcp.server import call_tool, register_all_tools

    register_all_tools()

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个会返回非标准退出码的 checker
        # testlib.h 的 quitf(_fail, ...) 会返回退出码 3+
        checker_code = '''
#include "testlib.h"
int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    // 强制返回 FAIL
    quitf(_fail, "Checker internal error");
    return 3;
}
'''
        result = await call_tool("checker_build", {
            "problem_dir": tmpdir,
            "code": checker_code,
            "test_scenarios": [
                {
                    "input": "1",
                    "contestant_output": "1",
                    "reference_output": "1",
                    "expected_verdict": "FAIL",
                },
            ],
        })

        assert result.isError is False
        test_results = result.structuredContent.get("test_results", [])
        if test_results:
            # 应该识别为 FAIL 而非 WA
            assert test_results[0].get("actual_verdict") == "FAIL"


def test_all_prompts_exist():
    """测试所有声明的 prompt 都存在。"""
    from autocode_mcp.prompts import get_prompt, list_prompts

    prompts = list_prompts()
    assert len(prompts) == 6

    for name in prompts:
        content = get_prompt(name)
        assert content, f"Prompt '{name}' is empty"
        assert len(content) > 100, f"Prompt '{name}' seems too short"
