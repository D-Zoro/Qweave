"""Normalized cost function for scheduling decisions."""

from typing import Dict, List, Tuple, Optional
import numpy as np
from qweave.crosstalk_model.graph import CrosstalkGraph


class CostFunction:
    """
    Normalized cost function for crosstalk-aware scheduling.

    Formula from Specification Section 15:
        cost = 1.0·depth_term + 0.5·gate_term + 2.0·error_term + 5.0·crosstalk_term

    Where:
        depth_term = (new_depth - current_depth) / 1
        gate_term = 1 / total_remaining_two_qubit_gates
        error_term = estimated_gate_error
        crosstalk_term = sum(interaction_weight) / max_observed_interaction
    """

    WEIGHTS = {
        "depth": 1.0,
        "gate": 0.5,
        "error": 2.0,
        "crosstalk": 5.0,
    }

    def __init__(
        self,
        crosstalk_graph: CrosstalkGraph,
        coupling_map: Optional[List[List[int]]] = None
    ):
        self.graph = crosstalk_graph
        self.coupling_map = coupling_map or []
        self.max_interaction = crosstalk_graph.get_max_interaction()

    def calculate(
        self,
        candidate_ops: List[int],
        current_ops: List[int],
        current_depth: int,
        remaining_gates: int,
        estimated_error: float = 0.001
    ) -> float:
        """
        Calculate cost of adding candidate operations to current layer.

        Args:
            candidate_ops: Operations being considered for addition
            current_ops: Operations already in current layer
            current_depth: Current circuit depth
            remaining_gates: Number of remaining two-qubit gates
            estimated_error: Baseline gate error estimate

        Returns:
            Total cost value (lower is better)
        """
        # Depth term: adding operations doesn't increase depth (parallel)
        # but we might need to account for serialization effects
        depth_term = 0.0  # Same layer = no depth increase

        # Gate term: prefer keeping gates if we have few remaining
        gate_term = 1.0 / max(remaining_gates, 1)

        # Error term: baseline error estimate
        error_term = estimated_error

        # Crosstalk term: sum of interactions between current and candidate ops
        crosstalk_sum = 0.0
        for candidate in candidate_ops:
            for current in current_ops:
                weight = self.graph.get_interaction_weight(candidate, current)
                crosstalk_sum += weight

        # Normalize by max observed interaction
        crosstalk_term = crosstalk_sum / max(self.max_interaction, 1e-6)

        # Compute weighted sum
        cost = (
            self.WEIGHTS["depth"] * depth_term +
            self.WEIGHTS["gate"] * gate_term +
            self.WEIGHTS["error"] * error_term +
            self.WEIGHTS["crosstalk"] * crosstalk_term
        )

        return cost

    def incremental_cost(
        self,
        operation: int,
        current_layer: List[int],
        remaining_ops: List[int]
    ) -> float:
        """
        Calculate incremental cost of adding operation to current layer.

        This is the primary interface for the greedy scheduler.
        """
        if not current_layer:
            # First operation in layer has no crosstalk penalty
            return self.WEIGHTS["error"] * 0.001

        # Calculate crosstalk with existing layer operations
        crosstalk_sum = sum(
            self.graph.get_interaction_weight(operation, existing)
            for existing in current_layer
        )

        crosstalk_term = crosstalk_sum / max(self.max_interaction, 1e-6)

        # Higher crosstalk = higher cost to add to this layer
        return self.WEIGHTS["crosstalk"] * crosstalk_term + self.WEIGHTS["error"] * 0.001

    def evaluate_schedule(
        self,
        schedule: List[List[int]],
        total_gates: int,
        estimated_errors: Optional[Dict[int, float]] = None
    ) -> Dict[str, float]:
        """
        Evaluate full schedule quality.

        Returns breakdown of cost components.
        """
        depth = len(schedule)
        total_crosstalk = 0.0

        for layer in schedule:
            # Sum all pairwise interactions in the layer
            for i, op_a in enumerate(layer):
                for op_b in layer[i + 1:]:
                    total_crosstalk += self.graph.get_interaction_weight(op_a, op_b)

        estimated_errors = estimated_errors or {}
        total_error = sum(estimated_errors.get(op, 0.001) for layer in schedule for op in layer)

        return {
            "depth": depth,
            "total_crosstalk": total_crosstalk,
            "total_error": total_error,
            "normalized_crosstalk": total_crosstalk / max(self.max_interaction, 1e-6),
            "cost": (
                self.WEIGHTS["depth"] * depth +
                self.WEIGHTS["gate"] * (1.0 / max(total_gates, 1)) +
                self.WEIGHTS["error"] * total_error / max(total_gates, 1) +
                self.WEIGHTS["crosstalk"] * total_crosstalk / len(schedule)
            )
        }