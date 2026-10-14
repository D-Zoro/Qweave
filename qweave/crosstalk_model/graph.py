"""NetworkX-based weighted interaction graph."""

from typing import Dict, Tuple, List, Optional, Any
import networkx as nx
import numpy as np
from qweave.crosstalk_model.matrix import InteractionMatrix


class CrosstalkGraph:
    """
    Weighted graph representation of crosstalk interactions.

    Mathematical representation: G_XT = (V, E, W)
    where:
        V = physical qubits or relevant operation locations
        E = potentially interacting pairs
        W(e) = estimated crosstalk/interference severity
    """

    def __init__(self, interaction_matrix: Optional[InteractionMatrix] = None):
        self.graph = nx.Graph()
        self.interaction_matrix = interaction_matrix

        if interaction_matrix:
            self._build_from_matrix(interaction_matrix)

    def _build_from_matrix(self, matrix: InteractionMatrix):
        """Construct graph from interaction matrix."""
        self.graph.clear()

        # Add nodes for each gate
        for i, label in enumerate(matrix.labels):
            self.graph.add_node(i, label=label, qubits=label)

        # Add edges for significant interactions
        for i in range(matrix.n):
            for j in range(i + 1, matrix.n):
                weight = matrix.matrix[i, j]
                if weight > 0:
                    self.graph.add_edge(i, j, weight=weight)

    def add_interaction(self, node_a: int, node_b: int, weight: float):
        """Add or update an interaction edge."""
        self.graph.add_edge(node_a, node_b, weight=weight)

    def get_interaction_weight(self, node_a: int, node_b: int) -> float:
        """Get weight of interaction between two nodes."""
        if self.graph.has_edge(node_a, node_b):
            return self.graph[node_a][node_b].get("weight", 0.0)
        return 0.0

    def get_neighbors_by_weight(self, node: int, threshold: float = 0.0) -> List[Tuple[int, float]]:
        """Get neighbors sorted by interaction weight."""
        neighbors = []
        for neighbor in self.graph.neighbors(node):
            weight = self.graph[node][neighbor]["weight"]
            if weight >= threshold:
                neighbors.append((neighbor, weight))

        return sorted(neighbors, key=lambda x: x[1], reverse=True)

    def get_weighted_degree(self, node: int) -> float:
        """Get sum of all interaction weights for a node."""
        if node not in self.graph:
            return 0.0
        return sum(data["weight"] for _, _, data in self.graph.edges(node, data=True))

    def get_max_interaction(self) -> float:
        """Get maximum interaction weight in the graph."""
        if not self.graph.edges():
            return 1.0  # Avoid division by zero
        return max(data["weight"] for _, _, data in self.graph.edges(data=True))

    def get_placement_cost(self, mapping: Dict[int, int]) -> float:
        """
        Calculate placement cost based on interaction graph.

        This is used by the placement optimizer to score mappings.
        """
        cost = 0.0
        for node_a, node_b, data in self.graph.edges(data=True):
            weight = data["weight"]
            # Check if mapped qubits are adjacent in coupling map
            # (This is simplified; full implementation needs coupling map)
            cost += weight
        return cost

    def to_networkx(self) -> nx.Graph:
        """Return the underlying NetworkX graph."""
        return self.graph

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "nodes": [
                {
                    "id": node,
                    "label": str(data.get("label", node)),
                    "qubits": list(data.get("qubits", []))
                }
                for node, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "weight": float(data["weight"])
                }
                for u, v, data in self.graph.edges(data=True)
            ]
        }

    @classmethod
    def from_matrix(cls, matrix: InteractionMatrix) -> "CrosstalkGraph":
        """Create graph from interaction matrix."""
        return cls(matrix)