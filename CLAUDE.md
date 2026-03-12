# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指导。

## 项目概述

ACMGO 是一个 AI 辅助的竞赛编程出题框架。它提供了创建高质量算法题目的 SOP（标准作业程序），包含自动化测试、数据生成和 Polygon 打包功能，以及完整的 AI Agent 实现。

## AI Agent 使用

当使用 Claude Code 时，你可以直接要求创建题目：

```
"出一个动态规划题目"
"出一个图论题目，要求求最短路"
```

Agent 会自动完成 6 步工作流程：
1. 题面设计
2. 解法实现（sol.cpp 和 brute.cpp）
3. 数据校验器（val.cpp）
4. 数据生成器（gen.cpp）
5. 压力测试（1000+ 轮对比）
6. Polygon 格式打包

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

## 常用命令

### 编译 C++ 文件
```bash
g++ -std=c++2c -O2 <file>.cpp -o <file>.exe
```

### 运行对拍测试（开发阶段）
在阶段一的题目根目录运行：
```bash
python stress.py
```
此命令会编译 gen、val、sol、brute 并使用小数据（N <= 100）运行 1000 轮验证。

### 生成测试数据（Polygon 格式）
在阶段二的题目根目录运行：
```bash
python scripts/gen_tests.py
```
生成 20 组测试数据（01.in 到 20.in）及其对应答案。

### 打包为 Polygon 格式
对拍测试通过后，在题目根目录运行：
```bash
python pack_polygon.py
```
将扁平结构的文件移动到 Polygon 目录结构，并清理开发文件。

## 数据生成器参数

生成器（`gen.exe`）接受以下参数：
```
gen.exe <seed> <type> <n_min> <n_max> <t_min> <t_max>
```

- `seed`: 随机种子（testlib 要求）
- `type`: 数据类型
  - 1 = 小数据 (N <= 10)
  - 2 = 随机数据
  - 3 = 大数据 (N 接近上限)
  - 4 = 边界情况（全相同、递增等）
  - 5 = 反hack 数据（用于破解错误解的特定模式）
- `n_min`, `n_max`: N 的范围
- `t_min`, `t_max`: T（测试用例数）的范围

## 出题工作流程

1. 确定题目核心算法和题面
2. 实现 `sol.cpp`（最优解）和 `brute.cpp`（验证用）
3. 使用 testlib 实现 `val.cpp` 以验证数据约束
4. 使用 testlib 实现 `gen.cpp`，支持多种数据类型（小数据、随机、大数据、边界、反hack）
5. 运行 `stress.py` - 必须通过 1000+ 轮小数据测试
6. 运行 `pack_polygon.py` 整理文件
7. 运行 `scripts/gen_tests.py` 生成最终测试数据

## 关键约束

- 对拍测试必须使用小数据（N <= 100），确保暴力解快速完成
- 所有 Python 脚本只使用标准库（无需 pip install）
- 脚本中包含 Windows 控制台 UTF-8 处理，确保兼容性
- 解法使用 C++2C 标准和快速 I/O
