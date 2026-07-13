"""LLM provider factory with lazy singleton and registry."""
import functools
from backend.config import LLM_PROVIDER, LLM_MODEL, LLM_MAX_TOKENS, LLM_TIMEOUT, LLM_MAX_RETRIES


class ProviderConfigurationError(ValueError):
    """Raised when provider configuration is invalid."""
    pass


def _create_groq_llm():
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        timeout=LLM_TIMEOUT,
        max_retries=LLM_MAX_RETRIES,
    )


_LLM_REGISTRY = {
    "groq": _create_groq_llm,
}


def register_llm_provider(name: str, factory):
    """Register a new LLM provider.
    
    Args:
        name: Provider name (e.g., "openai", "google", "anthropic")
        factory: Callable that returns an LLM instance
    """
    _LLM_REGISTRY[name] = factory


@functools.lru_cache(maxsize=1)
def get_llm():
    """Get the configured LLM instance (lazy singleton)."""
    factory = _LLM_REGISTRY.get(LLM_PROVIDER)
    if factory is None:
        raise ProviderConfigurationError(
            f"Unknown LLM provider: '{LLM_PROVIDER}'. "
            f"Available: {list(_LLM_REGISTRY.keys())}"
        )
    return factory()