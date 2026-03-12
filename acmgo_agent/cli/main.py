#!/usr/bin/env python3
"""
ACMGO 出题 AI Agent 的 CLI 入口点。

Usage:
    python -m acmgo_agent.cli.main "dynamic programming problem"
    python -m acmgo_agent.cli.main --provider anthropic "graph theory problem"
"""
import argparse
import sys
import os
import io

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from ..providers.factory import create_provider
from ..core.agent import ProblemSetterAgent
from ..config.settings import get_settings, print_settings


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ACMGO Problem Setter AI Agent - AI-assisted competitive programming problem setter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new problem using Anthropic Claude
  python -m acmgo_agent.cli.main "dynamic programming problem"

  # Use OpenAI instead
  python -m acmgo_agent.cli.main --provider openai "graph problem"

  # Specify custom working directory
  python -m acmgo_agent.cli.main --work-dir ./problems/my_problem "dp problem"

  # List available providers
  python -m acmgo_agent.cli.main --list-providers

Environment Variables:
  ANTHROPIC_API_KEY   Anthropic API key (for --provider anthropic)
  OPENAI_API_KEY       OpenAI API key (for --provider openai)
  ACMGO_PROVIDER       LLM provider (default: anthropic)
  ACMGO_MODEL         Model name (default: claude-opus-4-6)
  ACMGO_WORK_DIR      Working directory (default: ./problems/new_problem)
  ACMGO_MAX_RETRIES   Maximum retries for self-healing (default: 3)
  ACMGO_AUTO_PROGRESS  Auto-progress through stages (default: false)
  ACMGO_VERBOSE       Verbose output (default: true)
        """,
    )

    # Positional arguments
    parser.add_argument(
        "description",
        nargs="?",
        help="题目核心算法描述（如 'dynamic programming problem'）",
    )

    # Provider options
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default=None,
        help="LLM Provider (default: from ACMGO_PROVIDER env var or 'anthropic')",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM Model name (default: from ACMGO_MODEL env var)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API Key (default: from ANTHROPIC_API_KEY or OPENAI_API_KEY env var)",
    )

    # Agent options
    parser.add_argument(
        "--work-dir",
        default=None,
        help="工作目录（default: ./problems/new_problem）",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="最大重试次数（default: 3）",
    )
    parser.add_argument(
        "--auto-progress",
        action="store_true",
        help="自动进入下一步（default: false）",
    )
    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="禁用详细输出",
    )

    # Utility options
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="列出可用的 LLM Provider",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="显示当前配置",
    )

    args = parser.parse_args()

    # Handle utility commands
    if args.list_providers:
        print("可用的 LLM Provider:")
        print("  - anthropic: Anthropic Claude (需要 ANTHROPIC_API_KEY)")
        print("  - openai: OpenAI GPT (需要 OPENAI_API_KEY)")
        return 0

    # Get settings
    try:
        settings = get_settings(
            provider=args.provider,
            api_key=args.api_key,
            model=args.model,
            work_dir=args.work_dir,
            max_retries=args.max_retries,
            auto_progress=args.auto_progress,
            verbose=not args.no_verbose,
        )
    except ValueError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        return 1

    # Show config if requested
    if args.show_config:
        print_settings(settings)
        return 0

    # Validate API key
    if not settings.validate_api_key():
        print(
            f"错误: 未找到 {settings.provider} 的 API Key。",
            file=sys.stderr,
        )
        if settings.provider == "anthropic":
            print("请设置 ANTHROPIC_API_KEY 环境变量或使用 --api-key 参数。", file=sys.stderr)
        elif settings.provider == "openai":
            print("请设置 OPENAI_API_KEY 环境变量或使用 --api-key 参数。", file=sys.stderr)
        return 1

    # Check for problem description
    if not args.description:
        print("错误: 请提供题目核心算法描述。", file=sys.stderr)
        print("示例: python -m acmgo_agent.cli.main 'dynamic programming problem'", file=sys.stderr)
        return 1

    # Create provider
    try:
        provider = create_provider(
            settings.provider,
            api_key=settings.api_key,
            model=settings.model,
        )
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    # Create and run agent
    try:
        print(f"ACMGO Problem Setter AI Agent")
        print(f"工作目录: {settings.work_dir}")
        print(f"使用 Provider: {settings.provider} ({settings.model})")
        print("=" * 60)

        agent = ProblemSetterAgent(
            provider=provider,
            work_dir=settings.work_dir,
            max_retries=settings.max_retries,
            auto_progress=settings.auto_progress,
            verbose=settings.verbose,
        )

        result = agent.run(args.description)

        # Print results
        print("=" * 60)
        if result["status"] == "success":
            print(f"出题完成！文件保存在: {result['work_dir']}")
            return 0
        else:
            print(f"出题失败: {result.get('error', '未知错误')}")
            if "stage" in result:
                print(f"失败阶段: {result['stage']}")
            return 1

    except KeyboardInterrupt:
        print("\n用户中断。", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
