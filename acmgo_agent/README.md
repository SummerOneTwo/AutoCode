# ACMGO 出题 AI Agent

基于 ACMGO 框架的 AI 辅助竞赛编程出题助手。

## 概述

ACMGO Agent 是一个智能助手，帮助你创建高质量的算法编程题目，包含自动化测试、数据生成和 Polygon 打包功能。它遵循 ACMGO SOP（标准作业程序），提供完整的 6 步工作流程。

## 特性

- **自动化出题**：遵循 6 步工作流程创建完整题目
- **自愈机制**：自动检测并修复常见代码错误
- **多 LLM 支持**：支持 Anthropic Claude 和 OpenAI GPT 模型
- **Polygon 集成**：自动打包为 Polygon 格式
- **压力测试**：内置 1000+ 轮暴力验证支持

## 安装

```bash
# 使用 uv（推荐）
uv pip install -e acmgo_agent

# 或使用 pip
pip install -e acmgo_agent
```

## 快速开始

```bash
# 设置 API 密钥
export ANTHROPIC_API_KEY="your-api-key-here"

# 运行 Agent
python -m acmgo_agent.cli.main "动态规划问题"
```

## 使用方法

### 基本用法

```bash
python -m acmgo_agent.cli.main <题目描述>
```

### 选项

```bash
python -m acmgo_agent.cli.main <描述> [选项]

选项:
  --provider {anthropic,openai}  LLM 提供商（默认：anthropic）
  --model MODEL                 模型名称
  --api-key KEY                API 密钥
  --work-dir DIR               工作目录
  --max-retries N              自愈最大重试次数（默认：3）
  --auto-progress               自动进入下一步
  --no-verbose                 禁用详细输出
  --list-providers            列出可用的提供商
  --show-config               显示当前配置
```

### 示例

```bash
# 使用 Anthropic Claude 创建动态规划题目
python -m acmgo_agent.cli.main "最长上升子序列动态规划"

# 使用不同的工作目录
python -m acmgo_agent.cli.main --work-dir ./problems/lis "LIS 动态规划"

# 使用 OpenAI
python -m acmgo_agent.cli.main --provider openai "图遍历问题"

# 指定自定义模型
python -m acmgo_agent.cli.main --model claude-sonnet-4-6 "字符串匹配问题"
```

## 配置

Agent 可以通过环境变量进行配置：

| 变量 | 描述 | 默认值 |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | - |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `ACMGO_PROVIDER` | LLM 提供商 | `anthropic` |
| `ACMGO_MODEL` | 模型名称 | `claude-opus-4-6` |
| `ACMGO_WORK_DIR` | 工作目录 | `./problems/new_problem` |
| `ACMGO_MAX_RETRIES` | 自愈最大重试次数 | `3` |
| `ACMGO_AUTO_PROGRESS` | 自动进入下一步 | `false` |
| `ACMGO_VERBOSE` | 详细输出 | `true` |
| `ACMGO_COMPILER` | C++ 编译器 | `g++` |

## 工作流程

Agent 遵循 6 步工作流程：

1. **题面设计**：设计题目描述（输入/输出格式、样例）
2. **解法实现**：实现最优解（`sol.cpp`）和暴力解（`brute.cpp`）
3. **数据校验**：使用 testlib 实现数据校验器（`val.cpp`）
4. **数据生成**：实现数据生成器（`gen.cpp`），支持 5 种数据类型
5. **压力测试**：：运行 1000+ 轮对比测试，带自愈功能
6. **打包**：生成测试数据并打包为 Polygon 格式

## 自愈机制

当压力测试失败时，Agent 会：
1. 分析失败的输入和输出
2. 识别最优解中的错误
3. 自动修复代码
4. 重新运行压力测试
5. 重复直到达到最大重试限制（默认：3 次）

## 项目结构

完成后，题目按 Polygon 格式组织：

```
problem/
├── files/         ← testlib.h, gen.cpp, val.cpp
├── solutions/     ← sol.cpp, brute.cpp
├── statements/    ← README.md
├── scripts/       ← stress.py, gen_tests.py, cleanup.py
├── tests/         ← 生成的测试数据（01.in/01.ans 到 20.in/20.ans）
└── problem.xml    ← Polygon 配置
```

## 扩展性

### 自定义工具

```python
from acmgo_agent.tools.base import Tool
from acmgo_agent.core.agent import ProblemSetterAgent

class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="我的自定义工具",
            parameters={"param": {"type": "string"}},
        )

    def execute(self, param: str):
        return {"success": True, "result": param}

# 注册到 Agent
agent = ProblemSetterAgent(provider, work_dir)
agent.register_tool("my_custom_tool", MyCustomTool())
```

### 自定义提示词

```python
agent = ProblemSetterAgent(provider, work_dir)
agent.set_custom_system_prompt("额外指令...")
```

### 工作流程钩子

```python
def before_stage(stage: str, context: dict):
    print(f"开始阶段：{stage}")

def after_stage(stage: str, result: dict, context: dict):
    print(f"阶段 {stage} 完成：{result}")

agent = ProblemSetterAgent(provider, work_dir)
agent.set_hooks(before_stage=before_stage, after_stage=after_stage)
```

## 要求

- Python 3.10+
- g++ 编译器（用于编译 C++ 代码）
- ANTHROPIC_API_KEY 或 OPENAI_API_KEY

## 许可证

MIT License - 详见 LICENSE 文件
