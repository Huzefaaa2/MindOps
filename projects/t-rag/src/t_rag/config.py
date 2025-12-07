"""
Configuration definitions for the T‑RAG service.

All tunable parameters for the Trace‑Native RAG pipeline are kept in
dataclasses defined in this module.  Values can be supplied through
environment variables (prefixed with ``TRAG_``) or passed directly
into the dataclasses when constructing them.  Keeping configuration
settings in one place simplifies tuning and makes the code easier to
read and maintain.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """Configuration options for embedding and language models.

    Attributes:
        embedding_model_name: Name of the SentenceTransformer model used
            for computing vector embeddings from span summaries.  The
            default uses a lightweight model to balance performance and
            accuracy.  Can be overridden with the ``TRAG_EMBEDDING_MODEL``
            environment variable.
        top_k: Number of similar contexts to retrieve from the vector
            store when answering a query.  A higher value provides more
            context at the expense of additional tokens.  Controlled via
            the ``TRAG_TOP_K`` environment variable.
        openai_model_name: Name of the OpenAI chat model used for root
            cause reasoning.  Change this if you wish to use a different
            model via ``TRAG_OPENAI_MODEL``.
        openai_temperature: Sampling temperature for the LLM.  Lower
            values yield more deterministic outputs.  Controlled via
            ``TRAG_OPENAI_TEMPERATURE``.
    """

    embedding_model_name: str = field(
        default_factory=lambda: os.getenv(
            "TRAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
    )
    top_k: int = int(os.getenv("TRAG_TOP_K", 5))
    openai_model_name: str = field(
        default_factory=lambda: os.getenv("TRAG_OPENAI_MODEL", "gpt-3.5-turbo")
    )
    openai_temperature: float = float(os.getenv("TRAG_OPENAI_TEMPERATURE", 0.2))


@dataclass
class StoreConfig:
    """Configuration options for the vector memory store.

    Attributes:
        dimension: Dimensionality of the embedding vectors.  This is
            automatically set once the embedding model is loaded and
            therefore usually need not be specified manually.
        n_neighbors: Number of neighbours to return when querying the
            vector store.  Defaults to ``ModelConfig.top_k`` unless
            explicitly provided.
    """

    dimension: int | None = None
    n_neighbors: int | None = None


@dataclass
class TRAGConfig:
    """Top‑level configuration container for T‑RAG.

    This aggregates the model and store configuration sections into a
    single object.  Additional configuration groups can be added here
    in the future (for example, logging or tracing settings).
    """

    model: ModelConfig = field(default_factory=ModelConfig)
    store: StoreConfig = field(default_factory=StoreConfig)


def load_config() -> TRAGConfig:
    """Load configuration from environment variables and apply defaults.

    Returns:
        A fully‑populated :class:`TRAGConfig` object.  If the number of
        neighbours in the store configuration is not explicitly set,
        it is automatically assigned to the ``top_k`` value from the
        model configuration.
    """
    cfg = TRAGConfig()
    # If n_neighbors isn't explicitly set, default to top_k
    if cfg.store.n_neighbors is None:
        cfg.store.n_neighbors = cfg.model.top_k
    return cfg