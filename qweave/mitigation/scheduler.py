"""Crosstalk-aware greedy list scheduler."""

from typing import List, Dict, Set, Tuple, Optional
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit

from qweave.crosstalk_model.graph import CrosstalkGraph
from qweave.mitigation.cost_function import CostFunction


class CrosstalkScheduler:
    """
    Greedy list scheduler using normalized cost function.

    Algorithm (Section 15 specification):
    1. Identify operations whose dependencies are satisfied
    2. Create current execution layer
    3. Select feasible candidate operation
    4. Determine which ready operations can execute concurrently
    5. Calculate incremental cost of adding candidate to current layer
    6. Prefer candidate with lowest incremental cost
    7. Continue filling layer
    8. Start new layer when appropriate
    9. Repeat until all operations scheduled
    """

    def __init__(
        self,
        crosstalk_graph: CrosstalkGraph,
        coupling_map: Optional[List[List[int]]] = None
    ):
        self.graph = crosstalk_graph
        self.cost_fn = CostFunction(crosstalk_graph, coupling_map)

    def schedule(self, circuit: QuantumCircuit) -> List[List[int]]:
        """
        Schedule circuit operations into layers.

        Args:
            circuit: Input quantum circuit

        Returns:
            List of layers, each layer is a list of operation indices
        """
        dag = circuit_to_dag(circuit)

        # Map DAG nodes to indices
        node_to_idx = {}
        idx_to_node = {}
        for idx, node in enumerate(dag.op_nodes()):
            node_to_idx[node] = idx
            idx_to_node[idx] = node

        # Build dependencies: op_idx -> set of prerequisite op indices
        dependencies = self._build_dependencies(dag, node_to_idx)

        # Track scheduled and ready operations
        scheduled: Set[int] = set()
        schedule: List[List[int]] = []
        remaining: Set[int] = set(idx_to_node.keys())

        while remaining:
            # Find ready operations (all dependencies satisfied)
            ready = {
                idx for idx in remaining
                if dependencies[idx] <= scheduled
            }

            if not ready:
                # This shouldn't happen for valid DAGs
                raise RuntimeError("No ready operations but tasks remain")

            # Build current layer greedily
            layer: List[int] = []
            layer_remaining = list(ready)

            while layer_remaining:
                # Select operation with lowest incremental cost
                best_op = None
                best_cost = float('inf')

                for op_idx in layer_remaining:
                    cost = self.cost_fn.incremental_cost(op_idx, layer, list(remaining))
                    if cost < best_cost:
                        best_cost = cost
                        best_op = op_idx

                if best_op is None:
                    break

                layer.append(best_op)
                layer_remaining.remove(best_op)

                # Re-evaluate remaining operations
                # (their incremental cost changes as layer grows)

            # Commit layer to schedule
            schedule.append(layer)
            scheduled.update(layer)
            remaining -= set(layer)

        return schedule

    def _build_dependencies(
        self,
        dag: DAGCircuit,
        node_to_idx: Dict
    ) -> Dict[int, Set[int]]:
        """Build dependency graph from DAG."""
        dependencies = {idx: set() for idx in node_to_idx.values()}

        for node, idx in node_to_idx.items():
            for pred in dag.predecessors(node):
                if pred in node_to_idx:
                    dependencies[idx].add(node_to_idx[pred])

        return dependencies

    def schedule_to_circuit(
        self,
        original: QuantumCircuit,
        schedule: List[List[int]]
    ) -> QuantumCircuit:
        """
        Convert schedule back to circuit with barriers between layers.

        This introduces barriers to enforce the scheduled layer structure.
        """
        dag = circuit_to_dag(original)
        nodes = list(dag.op_nodes())

        # Map original node index to scheduled layer
        node_to_layer = {}
        for layer_idx, layer in enumerate(schedule):
            for op_idx in layer:
                node_to_layer[nodes[op_idx]] = layer_idx

        # Build new circuit layer by layer
        num_qubits = original.num_qubits
        num_clbits = original.num_clbits
        new_qc = QuantumCircuit(num_qubits, num_clbits, name=original.name)

        for layer_idx in range(len(schedule)):
            layer_ops = [n for n, l in node_to_layer.items() if l == layer_idx]

            # Add operations in layer
            for node in layer_ops:
                new_qc.append(node.op, node.qargs, node.cargs)

            # Add barrier between layers
            if layer_idx < len(schedule) - 1:
                new_qc.barrier()

        return new_qc