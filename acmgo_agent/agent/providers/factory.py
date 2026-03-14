"""
Factory for creating LLM provider instances.
"""
from typing import Optional
from .base import LLMProvider


def create_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        provider_name: Name of the "provider" (anthropic, openai, or litellm).
        api_key: Optional API key. If not provided, reads from environment variable.
        model: Optional model name. If not provided, uses default for provider.
        **kwargs: Additional provider-specific parameters.

    Returns:
        LLMProvider instance.

    Raises:
        ValueError: If provider_name is not recognized.
    """
    provider_name = provider_name.lower()

    if provider_name == "anthropic":
        from .anthropic import AnthropicProvider
        if model is None:
            model = kwargs.get("model", "claude-opus-4-6")
        return AnthropicProvider(api_key=api_key, model=model)
    elif provider_name == "openai":
        from .openai import OpenAIProvider
        if model is None:
            model = kwargs.get("model", "gpt-4o")
        return OpenAIProvider(api_key=api_key, model=model)
    elif provider_name == "litellm":
        from .litellm import LiteLLMProvider
        if model is None:
            model = kwargs.get("model", "anthropic/claude-opus-4-6")
        return LiteLLMProvider(
            api_key=api_key,
            model=model,
            rate_limit_min_interval=kwargs.get("rate_limit_min_interval", 0.05),
            **{k: v for k, v in kwargs.items() if k != "rate_limit_min_interval"}
        )
    else:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Supported providers: 'anthropic', 'openai', 'litellm'"
        )


def list_providers() -> list[str]:
    """List available provider names."""
    return ["anthropic", "openai", "litellm"]
