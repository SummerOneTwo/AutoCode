# ACMGO 出题 AI Agent

基于 ACMGO 框架的 AI 辅助的竞赛编程出题助手。

## 概述

ACMGO Agent 是一个智能助手，帮助你创建高质量的算法编程题目，包含自动化测试、数据生成和 Polygon 打包功能。它遵循 ACMGO SOP（标准作业程序），提供完整的 6 步工作流程。

## 特性

- **自动化出题**：遵循 6 步工作流程创建完整题目
- **自愈机制**：自动检测并修复常见代码错误
- **多 LLM 支持**：通过 LiteLLM 支持 100+ 提供商（Anthropic、OpenAI、Google、Cohere 等）
- **Polygon 集成**：自动打包为 Polygon 格式
- **压力测试**：内置 1000+ 轮暴力验证支持
- **完整测试套件**：包含 32 个 pytest 测试用例

## 安装

```bash
# 使用 uv（推荐）
uv pip install -e ./acmgo_agent

# 或使用 pip
pip install -e ./acmgo_agent
```

## 快速开始

### 配置环境

1. 复制示例配置文件：
```bash
cp .env.example .env
```

2. 编辑 `acmgo_agent/.env` 文件，填入你的 API 密钥和配置：
```bash
# 至少需要设置以下之一：
# LITELLM_API_KEY=your-api-key
# 或
# ANTHROPIC_API_KEY=your-anthropic-key
# OPENAI_API_KEY=your-openai-key
```

### 运行 Agent

```bash
# 基本用法
cd acmgo_agent
uv run python -m cli.main "动态规划问题"

# 或使用 .env 文件配置
uv run python -m cli.main --show-config  # 先检查配置
uv run python -m cli.main "动态规划问题"
```

## 使用方法

### 基本用法

```bash
python -m acmgo_agent.cli.main <题目描述>
```

### CLI 选项

```bash
python -m acmgo_agent.cli.main <描述> [选项]

选项:
  --provider {anthropic,openai,litellm}  LLM 提供商（默认：litellm）
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
uv run python -m cli.main "最长上升子序列动态规划"

# 使用不同的工作目录
uv run python -m cli.main --work-dir ../problems/lis "LIS 动态规划"

# 指定自定义模型
uv run python -m cli.main --model anthropic/claude-sonnet-4-6 "字符串匹配问题"
```

## 配置

### 使用 .env 文件（推荐）

在 `acmgo_agent/` 目录创建 `.env` 文件（可复制 `.env.example` 作为模板）：

```bash
cd acmgo_agent
cp .env.example .env
```

### 环境变量配置

Agent 也可以通过环境变量进行配置：

| 变量 | 描述 | 默认值 |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | - |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `GOOGLE_API_KEY` | Google API 密钥 | - |
| `COHERE_API_KEY` | Cohere API 密钥 | - |
| `LITELLM_API_KEY` | 通用 API 密钥（备用） | - |
| `ACMGO_PROVIDER` | LLM 提供商（anthropic/openai/litellm） | `litellm` |
| `ACMGO_MODEL` | 模型名称 | `anthropic/claude-opus-4-6` |
| `ACMGO_WORK_DIR` | 工作目录 | `./problems/new_problem` |
| `ACMGO_MAX_RETRIES` | 自愈最大重试次数 | `3` |
| `ACMGO_AUTO_PROGRESS` | 自动进入下一步 | `false` |
| `ACMGO_VERBOSE` | 详细输出 | `true` |
| `ACMGO_COMPILER` | C++ 编译器 | `g++` |

### 配置优先级

1. CLI 参数（`--provider`, `--api-key`, `--model` 等）
2. `.env` 文件中的变量
3. 系统环境变量
4. 默认值

## 工作流程

Agent 遵循 6 步工作流程：

1. **题面设计**：设计题目描述（输入/输出格式、样例）
2. **解法实现**：实现最优解（`sol.cpp`）和暴力解（`brute.cpp`）
3. **数据校验**：使用 testlib 实现数据校验器（`val.cpp`）
4. **数据生成**：实现数据生成器（`gen.cpp`），支持 5 种数据类型
5. **压力测试**：运行 1000+ 轮对比测试，带自愈功能
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

## 测试

运行完整测试套件：

```bash
cd acmgo_agent
uv run pytest tests/ -v --tb=short
```

测试覆盖：
- **核心代理测试** (6个)：初始化、工具注册、钩子系统、状态查询、自定义提示词
- **编译工具测试** (6个)：单文件编译、批量编译、错误处理
- **文件操作测试** (5个)：保存、读取、列出文件、集成测试
- **生成器测试** (2个)：测试数据生成
- **打包工具测试** (4个)：Polygon 格式打包、解包、目录结构
- **压力测试测试** (4个)：对拍测试、快速测试、参数验证
- **测试 Fixtures** (9个)：共享测试数据和工具

## 扩展性

### 自定义工具

```python
from acmgo_agent.agent.tools.base import Tool
from acmgo_agent.agent.core.agent import ProblemSetterAgent

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

### 工作流钩子

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
- LLM API 密钥（ANTHROPIC_API_KEY、OPENAI_API_KEY 或 LITELLM_API_KEY）

## LiteLLM 支持的模型

通过 `ACMGO_PROVIDER=litellm`，可以使用以下模型：

- **Anthropic**: `anthropic/claude-opus-4-6`, `anthropic/claude-sonnet-4-6`
- **OpenAI**: `openai/gpt-4o`, `openai/gpt-4-turbo`
- **Google**: `google/gemini-pro`
- **Cohere**: `cohere/command-r`
- 其他 100+ 提供商...

详见 https://docs.litellm.com/

## 许可证

MIT License - 详见 LICENSE 文件
