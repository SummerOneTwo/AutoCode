# Contributing to AutoCode MCP

感谢您有兴趣为 AutoCode MCP 做出贡献！

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/autocode-mcp.git
cd autocode-mcp

# 安装依赖
uv sync --all-extras
```

## 开发工作流

### 运行测试

```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov
```

### 代码质量

```bash
# 运行 lint 检查
make lint

# 格式化代码
make format

# 运行类型检查
make typecheck

# 运行所有检查
make check
```

## 项目结构

```
autocode_mcp/
├── src/autocode_mcp/     # 源代码
│   ├── tools/            # 工具实现
│   ├── utils/            # 工具函数
│   ├── resources/        # MCP Resources
│   ├── prompts/          # MCP Prompts
│   └── server.py         # MCP Server 入口
├── tests/                # 测试文件
├── templates/            # C++ 模板文件
├── pyproject.toml        # 项目配置
└── Makefile              # 开发命令
```

## 代码风格

- 使用 ruff 进行 lint 和格式化
- 使用 mypy 进行类型检查
- 遵循 PEP 8 规范
- 使用 f-string 格式化字符串
- 添加类型注解到公共 API

## 提交规范

使用 Conventional Commits:

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 重构
- `chore:` 其他更改

## Pull Request 流程

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 运行测试和 lint
5. 提交 Pull Request

## 问题反馈

请使用 GitHub Issues 报告问题或提出功能建议。
