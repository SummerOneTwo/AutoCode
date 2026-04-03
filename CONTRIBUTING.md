# 贡献指南 (Contributing to AutoCode)

由于 AutoCode 是一个旨在产出自动化高质量竞赛题目的辅助工具和 SOP 集合，我们非常珍惜所有形式的建议和改进。

## 提交 Issue

如果您发现了对拍脚本的 Bug、需要改进 SOP（Agent Prompt），请向我们**提交 Issue**，描述清楚：

1.  您所使用的环境（OS 及其版本、Python 版本等）。
2.  出现的具体问题（带上完整的报错日志）。
3.  您期望看到的结果。

## 提交 Pull Request

1.  **Fork 本仓库** 到您的账号下。
2.  新建一个分支用于您的修改：`git checkout -b feature/your-feature-name` 或 `fix/your-bugfix-name`。
3.  确保您的代码符合本指南和已有的风格规范。如果添加了 Python 脚本用于 Agent 或工具流程，请**确保在独立的 `uv` 环境下进行了良好测试**。
4.  提交您的修改。提交信息（Commit Message）需要尽量清晰明了。
5.  创建一个指向本仓库的 Pull Request。

## 开发规范提示

1.  **全局环境**：避免全局安装任何开发依赖，请使用项目内的独立虚拟隔离环境执行相关 Python 程序，并使用 `uv` 统一管理。
2.  **文件编码**：涉及 Windows 命令执行或文件生成的脚本时，请务必保证以 UTF-8 或相应无乱码编码执行。
3.  **遵循 SOP**：如果是针对核心 Agent Prompt 或 SOP 交互进行的改动，建议在拉取请求中附带通过跑通至少一次完整示例题型测试的运行截图。
