"""
Factory for creating LLM provider instances.
"""
from typing import Optional
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
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
        provider_name: Name of the provider ("anthropic" or "openai").
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
        if model is None:
            model = kwargs.get("model", "claude-opus-4-6")
        return AnthropicProvider(api_key=api_key, model=model)
    elif provider_name == "openai":
        if model is None:
            model = kwargs.get("model", "gpt-4o")
        return OpenAIProvider(api_key=api_key, model=model)
    else:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Supported providers: 'anthropic', 'openai'"
        )


def list_providers() -> list[str]:
    """List available provider names."""
    return ["anthropic", "openai"]
