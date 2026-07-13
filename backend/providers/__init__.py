"""Provider factory package."""
from backend.providers.embeddings import (
    get_embedding_provider,
    register_embedding_provider,
    ProviderConfigurationError as EmbeddingProviderConfigurationError,
)
from backend.providers.llm import (
    get_llm,
    register_llm_provider,
    ProviderConfigurationError as LLMProviderConfigurationError,
)

# Alias for common usage
ProviderConfigurationError = EmbeddingProviderConfigurationError

__all__ = [
    "get_embedding_provider",
    "get_llm",
    "register_embedding_provider",
    "register_llm_provider",
    "ProviderConfigurationError",
]