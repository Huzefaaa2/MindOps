"""
T‑RAG package initialization.

This package contains modules for the Trace‑Native Retrieval‑Augmented
Generation (T‑RAG) pipeline.  Importing this package makes it
possible to access the configuration, trace loading, vector memory,
language‑model reasoning and service orchestration components via
`t_rag.config`, `t_rag.trace_loader` and so forth.
"""

__all__ = [
    "config",
    "trace_loader",
    "vector_memory",
    "llm_reasoner",
    "service",
]