# ACMGO Single Agent 架构设计文档

本项目现有的交互 SOP (`.agent/rules/AGENTS.md`) 已经十分完善，覆盖了从核心算法出题、标程实现、暴力模拟到数据校验和压力对拍的完整流程。为了将上述流程自动化，将其进一步包装为一个功能强大的**单体 AI Agent (Single Unified Agent)** 将能显著减轻出题人的心智负担。

## 1. 核心目标

构建一个基于 Python 的单一职责 **Problem Setter Agent**，其主要能力是：
- 内化所有 `AGENTS.md` 的提示词逻辑。
- 获取强大的 `tools`（工具/函数）调用权限，以便实现与本地操作系统的完整交互（创建代码、编译 C++、执行对拍、读取日志）。
- 具备**自我反思和修正 (Self-Healing)** 机制，利用自动日志反馈优化失败的标程或生成器代码。

## 2. 系统架构设计

我们不采用复杂的 Multi-Agent 通信矩阵，而是依赖单一 Agent 循环的 **"思考(Think) -> 行动(Action/Tool) -> 观察(Observation)"** (ReAct) 工作流。

### 2.1 基础模块映射

| 当前 SOP 阶段 | Agent Tool/Action 映射设计 |
| :--- | :--- |
| **阶段一：题面设计** | Agent 内部思考并生成 `README.md` 内容，随后调用工具保存文件。 |
| **阶段二：双解法实现** | Agent 并行输出 `sol.cpp` 与 `brute.cpp` 的内容，并写入本地文件。 |
| **阶段三/四：校验器与生成器** | 生成 `val.cpp` 及 `gen.cpp`，利用 `testlib.h`。 |
| **阶段五：自动化对拍** | Agent 调用 `execute_stress_test()` 工具。该工具在后台通过 `subprocess` 运行 `stress.py` 或由 Agent 直接在 Python 中拉起本地 C++ 编译，并根据日志的 `stdout/stderr` 提取运行结果。 |
| **重试与排错 (关键补充)** | 若对拍失败（触发 WA, TLE 或编译错误），工具向 Agent 返回高亮错误的差异日志或编译日志。Agent 此时状态回流至思考阶段，重新给出 `xxx.cpp` 的修改方案，并再次调用验证工具（带有最大重试次数限制）。 |
| **阶段六：最终打包** | 所有流程通过且无错误反馈时，调用 `polygon_package()` 将所需文件复制、打包至目标 `.zip` 目录。 |

## 3. 技术选型与实现细节

由于用户限制必须使用 `uv`，且 Windows PowerShell 为核心环境，技术栈建议如下：

*   **包管理器**: `uv` (利用 `uv init` 和 `uv add` 可以极速搭建并隔离运行环境)。
*   **LLM 驱动库**: 推荐使用轻量级包装，如**原生的 OpenAI SDK (Python)** 结合 `tools` API，或利用类似于 `PydanticAI` 的强类型 Agent 框架以确保输出代码文件内容的高度一致性。这比部署完整的 LangChain 更加轻量且无黑盒逻辑。

### 3.1 核心 Tool 函数示例定义

为了能让单一 Agent 替代人工输入命令，至少需提供以下回调工具：
```python
def save_file(filename: str, content: str) -> str:
    """Agent 用于持久化代码结果的方法，可自动感知并保存到临时出题环境"""
    ...

def run_stress_test() -> dict:
    """Agent 执行该函数，本地自动调起 g++ 编译四套核心代码并执行测试。
    返回值需包含：成功与否(bool)、具体错误原因(若失败)、建议 Agent 修改的文件名。
    """
    ...
```

## 4. 后续开发路径

1. 初始化 Python 工程：使用 `uv init acmgo_agent`。
2. 将当前目录下的 `stress.py` 内核逻辑抽取为可供 Agent 回调并解析结构化数据的 Python 库函数。
3. 把 `AGENTS.md` 的内容切分为 System Prompt 和每个具体指令步骤的 Few-Shot 示例，灌入 `OpenAI` 客户端初始化流程。
4. 提供 CLI 命令行 `uv run acm_agent.py "出一个最小生成树并带边权查询的题"` 以测试整体流转。
