"""Crosstalk-aware qubit placement using 2-opt local search."""

import random
from typing import Dict, List, Tuple, Optional
from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap
from qiskit.transpiler.passes import SabreLayout
from qiskit.transpiler import PassManager

from qweave.crosstalk_model.graph import CrosstalkGraph


class CrosstalkPlacement:
    """
    2-opt local search for crosstalk-aware qubit placement.

    Algorithm (Section 13 specification):
    1. Initialize with Qiskit's default SabreLayout mapping
    2. Compute total interaction weight for adjacent mapped qubits
    3. Swap physical assignments iteratively
    4. Keep swaps that reduce the sum
    5. Stop when no swap improves cost or after 200 iterations
    """

    MAX_ITERATIONS = 200

    def __init__(
        self,
        crosstalk_graph: CrosstalkGraph,
        coupling_map: List[List[int]],
        max_iterations: int = MAX_ITERATIONS
    ):
        self.graph = crosstalk_graph
        self.coupling_map = set(tuple(sorted(pair)) for pair in coupling_map)
        self.max_iterations = max_iterations

    def optimize_placement(
        self,
        circuit: QuantumCircuit,
        initial_mapping: Optional[Dict[int, int]] = None
    ) -> Dict[int, int]:
        """
        Optimize logical-to-physical qubit mapping.

        Args:
            circuit: Circuit to place
            initial_mapping: Optional initial mapping (if None, uses SabreLayout)

        Returns:
            Optimized mapping dict: logical_qubit -> physical_qubit
        """
        if initial_mapping is None:
            mapping = self._get_sabre_mapping(circuit)
        else:
            mapping = initial_mapping.copy()

        logical_qubits = list(mapping.keys())

        # 2-opt local search
        improved = True
        iteration = 0
        current_cost = self._evaluate_mapping(mapping)

        while improved and iteration < self.max_iterations:
            improved = False
            iteration += 1

            # Try random swaps
            for _ in range(len(logical_qubits)):
                # Pick two random logical qubits to swap
                log_a, log_b = random.sample(logical_qubits, 2)

                # Swap and evaluate
                mapping[log_a], mapping[log_b] = mapping[log_b], mapping[log_a]
                new_cost = self._evaluate_mapping(mapping)

                if new_cost < current_cost:
                    # Keep the swap
                    current_cost = new_cost
                    improved = True
                else:
                    # Revert the swap
                    mapping[log_a], mapping[log_b] = mapping[log_b], mapping[log_a]

        return mapping

    def _get_sabre_mapping(self, circuit: QuantumCircuit) -> Dict[int, int]:
        """Get initial mapping from SabreLayout pass."""
        cmap = CouplingMap(couplinglist=list(self.coupling_map))

        # Create and run SabreLayout
        sabre = SabreLayout(coupling_map=cmap)
        pm = PassManager([sabre])
        _ = pm.run(circuit)

        # Extract initial layout if available
        layout = sabre.property_set.get("layout")
        if layout:
            return {
                logical: layout[logical]
                for logical in range(circuit.num_qubits)
            }

        # Fallback: identity mapping
        return {i: i for i in range(circuit.num_qubits)}

    def _evaluate_mapping(self, mapping: Dict[int, int]) -> float:
        """
        Evaluate mapping quality based on interaction graph.

        Lower cost is better. Considers interaction weights for
        physically adjacent qubits.
        """
        cost = 0.0

        # Sum interaction weights for mapped qubits that are adjacent
        for node_a, node_b, data in self.graph.graph.edges(data=True):
            weight = data["weight"]

            # Get physical assignments (extract integer indices from Qubit objects if needed)
            phys_a_raw = mapping.get(node_a, node_a)
            phys_b_raw = mapping.get(node_b, node_b)

            # Extract integer indices (support both int and Qubit objects)
            phys_a = getattr(phys_a_raw, '_index', phys_a_raw) if not isinstance(phys_a_raw, int) else phys_a_raw
            phys_b = getattr(phys_b_raw, '_index', phys_b_raw) if not isinstance(phys_b_raw, int) else phys_b_raw

            # Check if physical qubits are adjacent in coupling map
            if tuple(sorted([phys_a, phys_b])) in self.coupling_map:
                cost += weight

        return cost

    def apply_mapping(self, circuit: QuantumCircuit, mapping: Dict[int, int]) -> QuantumCircuit:
        """Apply mapping to circuit by reordering qubits."""
        # For MVP, just return info; full implementation needs transpilation
        mapped = circuit.copy()
        mapped.metadata = {"qubit_mapping": mapping}
        return mapped