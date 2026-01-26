"""Topology graph analysis and RCA hint generation."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .graph import TopologyGraph
from .ingest import edges_from_traces, load_manifests, nodes_from_manifests
from .models import Edge, GraphMetrics, Node, RCAHint, TopologyReport


class TopologyAnalyzer:
    def __init__(self, error_threshold: float = 0.05) -> None:
        self.error_threshold = error_threshold

    def analyze(
        self,
        manifest_paths: Optional[Iterable[str]] = None,
        trace_paths: Optional[Iterable[str]] = None,
    ) -> TopologyReport:
        graph = TopologyGraph()
        warnings: List[str] = []

        if manifest_paths:
            documents = load_manifests(manifest_paths)
            for node in nodes_from_manifests(documents):
                graph.add_node(node)
        else:
            warnings.append("No manifests provided; graph nodes will rely on trace data only.")

        edges, stats = ([], {})
        if trace_paths:
            edges, stats = edges_from_traces(trace_paths)
        else:
            warnings.append("No traces provided; edges and error metrics are empty.")

        name_to_node = {node.name: node.node_id for node in graph.nodes.values()}
        for edge in edges:
            source_id = name_to_node.get(edge.source, edge.source)
            target_id = name_to_node.get(edge.target, edge.target)
            if source_id not in graph.nodes:
                graph.add_node(_node_stub(source_id))
            if target_id not in graph.nodes:
                graph.add_node(_node_stub(target_id))
            graph.add_edge(Edge(source=source_id, target=target_id, label=edge.label, weight=edge.weight))

        degree = graph.degree_centrality()
        pagerank = graph.pagerank()
        error_rate = _error_rates(stats)

        metrics = GraphMetrics(
            degree_centrality=degree,
            pagerank=pagerank,
            error_rate=error_rate,
        )

        hints = _generate_hints(graph, metrics, self.error_threshold)

        return TopologyReport(
            nodes=list(graph.nodes.values()),
            edges=graph.edges,
            metrics=metrics,
            hints=hints,
            warnings=warnings,
        )


def _error_rates(stats: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    rates: Dict[str, float] = {}
    for service, entry in stats.items():
        total = entry.get("total", 0.0)
        errors = entry.get("errors", 0.0)
        rates[service] = (errors / total) if total else 0.0
    return rates


def _generate_hints(
    graph: TopologyGraph,
    metrics: GraphMetrics,
    threshold: float,
) -> List[RCAHint]:
    hints: List[RCAHint] = []
    pagerank = metrics.pagerank
    error_rate = metrics.error_rate

    max_pagerank = max(pagerank.values(), default=1.0)
    for node_id, node in graph.nodes.items():
        service_name = node.name
        service_error = error_rate.get(service_name, 0.0)
        service_rank = pagerank.get(node_id, 0.0)
        score = (service_error * 0.7) + ((service_rank / max_pagerank) * 0.3)
        notes = []
        if service_error >= threshold:
            notes.append(f"Error rate {service_error:.2%} exceeds threshold.")
        if service_rank >= max_pagerank * 0.6:
            notes.append("High topology centrality.")
        if notes:
            hints.append(
                RCAHint(
                    node_id=node_id,
                    service=service_name,
                    score=round(score, 4),
                    error_rate=round(service_error, 4),
                    pagerank=round(service_rank, 4),
                    notes=notes,
                )
            )
    hints.sort(key=lambda hint: hint.score, reverse=True)
    return hints


def _node_stub(service_name: str) -> Node:
    namespace = "unknown"
    name = service_name
    if "/" in service_name:
        namespace, name = service_name.split("/", 1)
    return Node(
        node_id=service_name,
        name=name,
        namespace=namespace,
        kind="Service",
        labels={},
    )
