"""
Root package for the T‑RAG implementation.

This directory is structured as a Python package to allow running
modules under the `t_rag` namespace.  For example, you can execute
the service CLI with:

```
python -m t_rag.service --trace path/to/trace.json
```

The `t_rag` package itself lives inside this directory and contains
the individual components of the Trace‑Native Retrieval‑Augmented
Generation pipeline.
"""

__all__ = ["t_rag"]