"""
ACMGO Agent 的配置管理。

设置可以通过以下方式提供：
1. .env 文件（自动加载）
2. 环境变量
3. 配置文件（可选）
4. 构造函数参数
"""
import os
from dataclasses import dataclass, field
from typing import Optional

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv

    # settings.py 位于 acmgo_agent/config/settings.py
    # 向上两级到 acmgo_agent 目录，向上三级到项目根目录
    config_dir = os.path.dirname(os.path.abspath(__file__))
    acmgo_agent_dir = os.path.dirname(config_dir)
    project_root = os.path.dirname(acmgo_agent_dir)

    # 搜索顺序：当前目录 -> acmgo_agent 目录 -> 项目根目录
    search_paths = [
        ".env",  # 当前工作目录
        os.path.join(acmgo_agent_dir, ".env"),  # acmgo_agent 目录
        os.path.join(project_root, ".env"),  # 项目根目录（向后兼容）
    ]

    for path in search_paths:
        if os.path.exists(path):
            load_dotenv(path)
            break
except ImportError:
    # python-dotenv 未安装，忽略
    pass


@dataclass
class AgentSettings:
    """
    Agent 设置和配置。

    属性从环境变量读取，带默认值。
    """

    # LLM Provider Settings
    provider: str = field(default_factory=lambda: os.getenv("ACMGO_PROVIDER", "litellm"))
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("LITELLM_API_KEY") or
        os.getenv("ANTHROPIC_API_KEY") or
        os.getenv("OPENAI_API_KEY")
    )
    model: str = field(default_factory=lambda: os.getenv("ACMGO_MODEL", "anthropic/claude-opus-4-6"))

    # Agent Behavior
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("ACMGO_MAX_RETRIES", "3"))
    )
    auto_progress: bool = field(
        default_factory=lambda: os.getenv("ACMGO_AUTO_PROGRESS", "false").lower() == "true"
    )
    verbose: bool = field(
        default_factory=lambda: os.getenv("ACMGO_VERBOSE", "true").lower() == "true"
    )

    # Testing Settings
    stress_trials: int = field(
        default_factory=lambda: int(os.getenv("ACMGO_STRESS_TRIALS", "1000"))
    )
    stress_n_max: int = field(
        default_factory=lambda: int(os.getenv("ACMGO_STRESS_N_MAX", "100"))
    )
    stress_t_max: int = field(
        default_factory=lambda: int(os.getenv("ACMGO_STRESS_T_MAX", "3"))
    )

    # Test Generation Settings
    test_count: int = field(
        default_factory=lambda: int(os.getenv("ACMGO_TEST_COUNT", "20"))
    )

    # Rate Limiting Settings
    rate_limit_min_interval: float = field(
        default_factory=lambda: float(os.getenv("ACMGO_RATE_LIMIT_MIN_INTERVAL", "0.05"))
    )

    # Working Directory
    work_dir: str = field(
        default_factory=lambda: os.getenv("ACMGO_WORK_DIR", "./problems/new_problem")
    )

    # Compiler Settings
    compiler: str = field(default_factory=lambda: os.getenv("ACMGO_COMPILER", "g++"))

    # Custom System Prompt (optional)
    custom_system_prompt: Optional[str] = field(
        default_factory=lambda: os.getenv("ACMGO_SYSTEM_PROMPT")
    )

    def __post_init__(self):
        """初始化后验证设置。"""
        if self.max_retries < 0:
            raise ValueError("max_retries 必须是非负数")

        if self.stress_trials < 1:
            raise ValueError("stress_trials 必须至少为 1")

        if self.test_count < 1:
            raise ValueError("test_count 必须至少为 1")

    @classmethod
    def from_env(cls) -> "AgentSettings":
        """
        仅从环境变量创建设置。

        当所有配置都来自环境时很有用。
        """
        return cls()

    @classmethod
    def from_dict(cls, config: dict) -> "AgentSettings":
        """
        从字典创建设置。

        环境变量用作未在 dict 中的值的默认值。
        """
        env_settings = cls.from_env().__dict__

        # 合并配置字典与环境默认值
        merged = {**env_settings, **config}

        return cls(**merged)

    def to_dict(self) -> dict:
        """将设置转换为字典（为安全隐藏 api_key）。"""
        result = {}
        for key, value in self.__dict__.items():
            # 隐藏敏感数据如 api_key
            if key == "api_key" and value is not None:
                result[key] = "***HIDDEN***"
            else:
                result[key] = value
        return result

    def validate_api_key(self) -> bool:
        """检查是否已配置 API 密钥。"""
        # For litellm, check various environment variables based on model prefix
        if self.provider == "litellm":
            # Extract provider from model name
            provider_from_model = self.model.split("/")[0].lower() if "/" in self.model else None

            # Map provider names to env vars
            env_vars = ["LITELLM_API_KEY"]
            if provider_from_model == "anthropic":
                env_vars.append("ANTHROPIC_API_KEY")
            elif provider_from_model == "openai":
                env_vars.append("OPENAI_API_KEY")
            elif provider_from_model == "google":
                env_vars.append("GOOGLE_API_KEY")
            elif provider_from_model == "cohere":
                env_vars.append("COHERE_API_KEY")

            # Check if any of the relevant env vars are set
            for env_var in env_vars:
                key = os.getenv(env_var)
                if key and len(key) > 0:
                    return True
            return False

        # For other providers, check api_key directly
        if self.api_key is None:
            return False

        # 非空字符串检查
        if isinstance(self.api_key, str) and len(self.api_key) > 0:
            return True

        return False


def get_settings(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> AgentSettings:
    """
    获取带可选覆盖的设置。

    Args:
        provider: 覆盖提供商名称。
        api_key: 覆盖 API 密钥。
        model: 覆盖模型名称。
        **kwargs: 额外设置覆盖。

    Returns:
        AgentSettings 实例。
    """
    # 从环境创建基础设置
    settings = AgentSettings.from_env()

    # 应用覆盖
    if provider is not None:
        settings.provider = provider
    if api_key is not None:
        settings.api_key = api_key
    if model is not None:
        settings.model = model

    # 应用额外覆盖（只在值不为 None 时覆盖）
    for key, value in kwargs.items():
        if hasattr(settings, key) and value is not None:
            setattr(settings, key, value)

    return settings


def print_settings(settings: AgentSettings) -> None:
    """以可读格式打印设置。"""
    print("ACMGO Agent 配置:")
    print("=" * 40)

    for key, value in settings.to_dict().items():
        print(f"  {key}: {value}")

    print("=" * 40)
