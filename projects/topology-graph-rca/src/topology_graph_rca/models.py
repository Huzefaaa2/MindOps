"""Models for Topology Graph RCA."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Node:
    node_id: str
    name: str
    namespace: str
    kind: str
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    label: str = "calls"
    weight: float = 1.0


@dataclass
class GraphMetrics:
    degree_centrality: Dict[str, float]
    pagerank: Dict[str, float]
    error_rate: Dict[str, float]


@dataclass
class RCAHint:
    node_id: str
    service: str
    score: float
    error_rate: float
    pagerank: float
    notes: List[str]


@dataclass
class TopologyReport:
    nodes: List[Node]
    edges: List[Edge]
    metrics: GraphMetrics
    hints: List[RCAHint]
    warnings: List[str] = field(default_factory=list)
