"""Embedding provider factory with lazy singleton and registry."""
import functools
from backend.config import EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_LOCAL_FILES_ONLY


class ProviderConfigurationError(ValueError):
    """Raised when provider configuration is invalid."""
    pass


def _create_huggingface_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"local_files_only": EMBEDDING_LOCAL_FILES_ONLY},
    )


_EMBEDDING_REGISTRY = {
    "huggingface": _create_huggingface_embeddings,
}


def register_embedding_provider(name: str, factory):
    """Register a new embedding provider.
    
    Args:
        name: Provider name (e.g., "openai", "google")
        factory: Callable that returns an embedding instance
    """
    _EMBEDDING_REGISTRY[name] = factory


@functools.lru_cache(maxsize=1)
def get_embedding_provider():
    """Get the configured embedding provider instance (lazy singleton)."""
    factory = _EMBEDDING_REGISTRY.get(EMBEDDING_PROVIDER)
    if factory is None:
        raise ProviderConfigurationError(
            f"Unknown embedding provider: '{EMBEDDING_PROVIDER}'. "
            f"Available: {list(_EMBEDDING_REGISTRY.keys())}"
        )
    return factory()