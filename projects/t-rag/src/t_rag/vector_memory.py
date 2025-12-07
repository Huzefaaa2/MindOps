"""
vector_memory.py
================

This module provides an in‑memory vector store for T‑RAG.  Its
responsibility is to hold embedding vectors together with associated
metadata (such as span records) and to support nearest‑neighbour
queries over those vectors.  The implementation is based on
scikit‑learn’s :class:`~sklearn.neighbors.NearestNeighbors`, which is
adequate for prototyping and small datasets.  For production
deployments handling millions of vectors you should consider using a
dedicated vector database such as FAISS, Milvus or Pinecone.
"""
from __future__ import annotations

from typing import List, Dict, Any, Iterable, Tuple

import numpy as np
from sklearn.neighbors import NearestNeighbors


class VectorMemoryStore:
    """A simple vector memory store using scikit‑learn's nearest neighbour index.

    Each entry in the store consists of a vector embedding and an
    associated metadata object.  Embeddings are stored in a NumPy
    array of shape ``(n_samples, dim)``, and a :class:`~sklearn.neighbors.NearestNeighbors`
    index is rebuilt when new items are added.  Although this is
    inefficient for very large datasets, it simplifies the API and
    allows for rapid prototyping.  For larger or more dynamic
    workloads, replace this class with an interface to an external
    vector database.
    """

    def __init__(self, dimension: int, n_neighbors: int = 5) -> None:
        self.dimension = dimension
        self.n_neighbors = n_neighbors
        # Internal storage for embeddings and metadata.  We start with
        # an empty array of the correct dimensionality to simplify
        # concatenation later on.
        self._embeddings: np.ndarray = np.empty((0, dimension), dtype=np.float32)
        self._metadata: List[Any] = []
        self._index: NearestNeighbors | None = None

    def add(self, embeddings: Iterable[np.ndarray], metadata: Iterable[Any]) -> None:
        """Add a batch of embeddings and their metadata to the store.

        Args:
            embeddings: Iterable of 1‑D NumPy arrays, each of length
                ``self.dimension``.
            metadata: Iterable of objects associated with each
                embedding.  Must have the same length as
                ``embeddings``.
        """
        emb_list = list(embeddings)
        meta_list = list(metadata)
        if len(emb_list) != len(meta_list):
            raise ValueError("embeddings and metadata must have the same length")
        if not emb_list:
            return
        # Stack embeddings into a 2D array and append
        emb_array = np.vstack([np.array(e, dtype=np.float32) for e in emb_list])
        if self._embeddings.size == 0:
            self._embeddings = emb_array
        else:
            self._embeddings = np.vstack([self._embeddings, emb_array])
        self._metadata.extend(meta_list)
        # Rebuild the nearest neighbour index whenever new data is added
        self._build_index()

    def _build_index(self) -> None:
        """Construct or rebuild the nearest neighbour index."""
        if self._embeddings.shape[0] == 0:
            # Nothing to build
            return
        self._index = NearestNeighbors(
            n_neighbors=min(self.n_neighbors, len(self._metadata)),
            metric="cosine",
            algorithm="auto",
        )
        self._index.fit(self._embeddings)

    def query(self, embedding: np.ndarray, k: int | None = None) -> List[Tuple[Any, float]]:
        """Query the store for the nearest neighbours of a given embedding.

        Args:
            embedding: A single embedding vector of shape ``(dimension,)``.
            k: The number of neighbours to retrieve.  Defaults to
                ``self.n_neighbors``.

        Returns:
            A list of tuples ``(metadata, distance)`` sorted by ascending
            distance (cosine distance).  Smaller distances indicate
            higher similarity.
        """
        if self._index is None:
            return []
        num_neighbors = k or self.n_neighbors
        # scikit‑learn returns arrays of shape (1, k)
        distances, indices = self._index.kneighbors([embedding], n_neighbors=num_neighbors)
        results: List[Tuple[Any, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            results.append((self._metadata[idx], float(dist)))
        return results