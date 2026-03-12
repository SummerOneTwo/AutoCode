# ACMGO

**ACMGO** (AI-assisted Competitive programming Problem Setter) 是一个基于大语言模型（LLM）的自动化竞赛出题与验题标准作业程序（SOP）和配套工具库。该项目旨在帮助专家和各类竞赛（如 ICPC、CCPC）出题人高效产出极强数据、毫无破绽的算法题目。

## 特性

- **自动化测试网络**：集成了对拍系统 (`stress.py`)，全自动实现解法验证，确保核心思路的正确性
- **严谨的数据校验**：内置 `testlib.h` 支持的数据生成器与校验器
- **标准化打包流程**：符合 Polygon 系统的标准目录结构和 `.xml` 配置，一键出题归档
- **智能化协同**：提供完整的 AI Agent 实现 ([详情参考 `acmgo_agent/`](acmgo_agent/))，支持自动生成和验证题目

## 目录结构

```text
ACMGO/
├── .agent/               # Agent 规则配置（用于 Claude Code 等工具）
├── .github/              # GitHub 社区模板与配置
├── acmgo_agent/          # AI Agent 实现（独立 Python 包）
├── docs/                 # 项目相关的设计文档与说明
├── problems/             # 整理好的各算法题目存放目录
│   ├── tower_construction/
│   └── trade_zone/
├── CLAUDE.md             # Claude Code 项目指令
├── CONTRIBUTING.md       # 贡献指南
├── LICENSE               # MIT 许可证
└── README.md             # 本说明文档
```

## 题目结构

每个题目遵循两阶段工作流程：

### 阶段一：开发阶段（扁平结构）
所有文件在同一目录，便于调试：
```
problem/
├── testlib.h      # Testlib 库
├── gen.cpp        # 数据生成器
├── val.cpp        # 数据校验器
├── sol.cpp        # 主解法（最优解）
├── brute.cpp      # 暴力解（用于验证）
├── stress.py      # 对拍脚本
└── README.md      # 题面描述
```

### 阶段二：Polygon 格式（打包后的结构）
开发和验证完成后，组织为：
```
problem/
├── files/         # testlib.h, gen.cpp, val.cpp
├── solutions/     # sol.cpp, brute.cpp
├── statements/    # README.md
├── scripts/       # stress.py, gen_tests.py, cleanup.py
├── tests/         # 生成的测试数据 (XX.in/XX.ans)
└── problem.xml    # Polygon 配置
```

## 出题工作流程

1. 确定题目核心算法和题面
2. 实现 `sol.cpp`（最优解）和 `brute.cpp`（验证用）
3. 使用 testlib 实现 `val.cpp` 以验证数据约束
4. 使用 testlib 实现 `gen.cpp`，支持多种数据类型（小数据、随机、大数据、边界、反hack）
5. 运行 `stress.py` - 必须通过 1000+ 轮小数据测试
6. 运行 `pack_polygon.py` 整理文件
7. 运行 `scripts/gen_tests.py` 生成最终测试数据

## 使用 AI Agent

项目提供了完整的 AI Agent 实现，支持自动生成和验证题目：

```bash
# 使用 Claude Code 时，只需输入题目描述
# "出一个动态规划题目"

# 或使用 CLI 模式（需先安装）
python -m acmgo_agent.cli.main "最长上升子序列动态规划"
```

详见 [acmgo_agent/README.md](acmgo_agent/README.md)。

## 贡献指南

我们欢迎并鼓励各种形式的贡献！请阅读我们的 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何为您发现的 Bug 提出 Issue，或通过 Pull Request 提供改进。

## 许可证

本项目遵从 [MIT License](LICENSE)。
