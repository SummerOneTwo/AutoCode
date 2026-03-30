# AutoCode MCP Server

基于论文《AutoCode: LLMs as Problem Setters for Competitive Programming》(arXiv:2510.12803) 实现的 MCP 工具服务器。

## 核心特性

- **Validator-Generator-Checker 框架**：完整实现论文的核心算法
- **14 个原子工具**：覆盖出题全流程
- **纯工具模式**：Server 不调用任何 LLM，由 Client 提供智能编排
- **安全隔离**：编译和执行带超时和资源限制

## 安装

```bash
cd autocode_mcp
uv sync
```

## 使用

### 作为 MCP Server 运行

```bash
uv run autocode-mcp
```

### 在 Claude Code 中配置

在 `.claude/settings.json` 中添加：

```json
{
  "mcpServers": {
    "autocode": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/autocode_mcp", "autocode-mcp"]
    }
  }
}
```

## 工具列表

### File 工具组
- `file_read` - 读取文件内容
- `file_save` - 保存文件内容

### Solution 工具组
- `solution_build` - 构建并编译解法
- `solution_run` - 运行解法

### Stress Test 工具组
- `stress_test_run` - 运行对拍测试

### Problem 工具组
- `problem_create` - 创建题目目录结构
- `problem_generate_tests` - 生成测试数据
- `problem_pack_polygon` - 打包为 Polygon 格式

### Validator 工具组
- `validator_build` - 构建并验证数据校验器
- `validator_select` - 选择最优 Validator

### Generator 工具组
- `generator_build` - 构建数据生成器
- `generator_run` - 运行多策略数据生成

### Checker 工具组
- `checker_build` - 构建并验证输出检查器

### Interactor 工具组
- `interactor_build` - 构建并验证交互器

## 工作流示例

### 完整出题流程

```
1. problem_create          # 创建题目目录
2. file_save               # 保存题面
3. solution_build (sol)    # 构建标准解法
4. solution_build (brute)  # 构建暴力解法
5. validator_build         # 构建数据校验器
6. generator_build         # 构建数据生成器
7. stress_test_run         # 运行对拍测试
8. problem_generate_tests  # 生成测试数据
9. problem_pack_polygon    # 打包为 Polygon 格式
```

## 设计原则

1. **Server 不调用 LLM**：所有代码生成由 Client LLM 完成
2. **无状态**：每次调用独立，状态由 `problem_dir` 管理
3. **统一返回格式**：`{success, error, data}`

## 参考

- [AutoCode 论文](https://arxiv.org/abs/2510.12803)
- [MCP 协议](https://modelcontextprotocol.io/)
- [testlib.h](https://github.com/MikeMirzayanov/testlib)
