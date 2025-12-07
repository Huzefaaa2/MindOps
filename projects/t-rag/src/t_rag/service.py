"""
service.py
==========

Entry point and orchestrator for the T‑RAG pipeline.  This module
ties together the configuration loading, trace parsing, embedding,
vector storage and language model reasoning into a single function
(``run``) and a command‑line interface (``_cli``).

You can run this module directly with a JSON trace file to obtain a
root cause hypothesis::

    python -m t_rag.service --trace path/to/trace.json

In a larger system you might import the ``run`` function and expose
it via a REST API, message bus or other interface.  See the README
for integration guidance and how to extend this pipeline for
production use.
"""
from __future__ import annotations

import argparse
import json
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import load_config
from .trace_loader import TraceLoader, SpanRecord
from .vector_memory import VectorMemoryStore
from .llm_reasoner import LLMReasoner


def embed_messages(model: SentenceTransformer, records: List[SpanRecord]) -> np.ndarray:
    """Compute embeddings for a list of span records.

    Args:
        model: A ``SentenceTransformer`` instance.
        records: A list of :class:`SpanRecord` objects to embed.

    Returns:
        A 2‑D NumPy array of shape ``(len(records), dim)`` containing
        the normalised vector embeddings.
    """
    texts = [rec.message for rec in records]
    # ``encode`` returns a list of vectors.  ``convert_to_numpy`` ensures
    # a NumPy array and ``normalize_embeddings`` scales vectors to unit length.
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def run(trace_path: str) -> Dict[str, Any]:
    """Execute the T‑RAG pipeline for a given trace file.

    This function orchestrates the entire pipeline: it loads
    configuration, instantiates the embedding model and vector store,
    parses the trace into records, computes embeddings, retrieves
    similar contexts and finally invokes the LLM for a root cause
    report.

    Args:
        trace_path: Path to a JSON file containing the spans for the
            current incident.

    Returns:
        A dictionary containing the root cause analysis result.  See
        :meth:`t_rag.llm_reasoner.LLMReasoner.generate_root_cause` for
        the returned schema.
    """
    cfg = load_config()
    # Load the embedding model specified in the configuration
    model = SentenceTransformer(cfg.model.embedding_model_name)
    # Populate the vector dimension once the model is initialised
    cfg.store.dimension = model.get_sentence_embedding_dimension()
    vstore = VectorMemoryStore(dimension=cfg.store.dimension, n_neighbors=cfg.store.n_neighbors)
    # Load current spans
    loader = TraceLoader(trace_path)
    records = loader.load_spans()
    # Compute embeddings and add them to the vector store.  In many
    # situations you may want to add current spans after analysis to
    # avoid biasing retrieval with the spans themselves; this example
    # inserts them immediately for simplicity.
    embeddings = embed_messages(model, records)
    vstore.add(embeddings, [rec.__dict__ for rec in records])
    # Retrieve similar contexts.  We query the store with each current
    # embedding and aggregate unique metadata entries.  In a real
    # deployment you might maintain a persistent store across incidents
    # and implement more sophisticated aggregation (e.g. deduplication
    # based on trace ID).
    retrieved: List[Dict[str, Any]] = []
    for emb in embeddings:
        neighbours = vstore.query(emb, k=cfg.model.top_k)
        for meta, _dist in neighbours:
            if meta not in retrieved:
                retrieved.append(meta)
    # Perform reasoning using the language model
    reasoner = LLMReasoner(cfg.model)
    result = reasoner.generate_root_cause(
        current_spans=[rec.__dict__ for rec in records],
        retrieved_contexts=retrieved,
    )
    return result


def _cli() -> None:
    """Command‑line interface for analysing a single trace file."""
    parser = argparse.ArgumentParser(description="Trace‑Native RAG root cause analysis")
    parser.add_argument(
        "--trace",
        required=True,
        help="Path to the JSON file containing spans for the current incident",
    )
    args = parser.parse_args()
    result = run(args.trace)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli()