"""Graph utilities for topology RCA."""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from .models import Edge, Node


class TopologyGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adj: Dict[str, List[str]] = {}

    def add_node(self, node: Node) -> None:
        if node.node_id not in self.nodes:
            self.nodes[node.node_id] = node
        self._adj.setdefault(node.node_id, [])

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
        self._adj.setdefault(edge.source, []).append(edge.target)

    def degree_centrality(self) -> Dict[str, float]:
        if not self.nodes:
            return {}
        counts = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            counts[edge.source] += 1
            counts[edge.target] += 1
        scale = max(1, len(self.nodes) - 1)
        return {node_id: count / scale for node_id, count in counts.items()}

    def pagerank(self, damping: float = 0.85, iterations: int = 20) -> Dict[str, float]:
        node_ids = list(self.nodes.keys())
        if not node_ids:
            return {}
        n = len(node_ids)
        rank = {node_id: 1.0 / n for node_id in node_ids}
        out_degree = {node_id: len(self._adj.get(node_id, [])) for node_id in node_ids}
        for _ in range(iterations):
            new_rank = {node_id: (1.0 - damping) / n for node_id in node_ids}
            for node_id in node_ids:
                targets = self._adj.get(node_id, [])
                if not targets:
                    for dest in node_ids:
                        new_rank[dest] += damping * rank[node_id] / n
                else:
                    share = damping * rank[node_id] / out_degree[node_id]
                    for dest in targets:
                        new_rank[dest] += share
            rank = new_rank
        return rank

    def to_dot(self) -> str:
        lines = ["digraph topology {"]
        for node in self.nodes.values():
            label = f"{node.name}\\n({node.namespace})"
            lines.append(f"  \"{node.node_id}\" [label=\"{label}\"];\n")
        for edge in self.edges:
            lines.append(f"  \"{edge.source}\" -> \"{edge.target}\" [label=\"{edge.label}\"];\n")
        lines.append("}")
        return "".join(lines)
