"""Main mitigation engine orchestrating placement and scheduling."""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from qiskit import QuantumCircuit
from qiskit.transpiler import TranspilerError

from qweave.crosstalk_model.graph import CrosstalkGraph
from qweave.mitigation.placement import CrosstalkPlacement
from qweave.mitigation.scheduler import CrosstalkScheduler


@dataclass
class MitigationResult:
    """Result of applying Q-Weave mitigation to a circuit."""
    original_circuit: QuantumCircuit
    mitigated_circuit: QuantumCircuit
    qubit_mapping: Dict[int, int]
    schedule: List[List[int]]
    metrics: Dict[str, Any]


class MitigationEngine:
    """
    Main engine for crosstalk-aware mitigation.

    Orchestrates the placement and scheduling phases based on
    the crosstalk interaction graph.
    """

    def __init__(
        self,
        crosstalk_graph: CrosstalkGraph,
        coupling_map: List[List[int]],
        initial_layout: Optional[Dict[int, int]] = None
    ):
        self.graph = crosstalk_graph
        self.coupling_map = coupling_map
        self.initial_layout = initial_layout

        self.placement = CrosstalkPlacement(crosstalk_graph, coupling_map)
        self.scheduler = CrosstalkScheduler(crosstalk_graph, coupling_map)

    def mitigate(self, circuit: QuantumCircuit) -> MitigationResult:
        """
        Apply full Q-Weave mitigation to a circuit.

        Steps:
        1. Optimize qubit placement
        2. Apply placement to circuit
        3. Schedule operations with crosstalk awareness
        4. Return mitigated circuit with metadata
        """
        # Step 1: Optimize placement
        mapping = self.placement.optimize_placement(circuit, self.initial_layout)

        # Step 2: Apply placement (logical to physical mapping)
        placed_circuit = self._apply_placement(circuit, mapping)

        # Step 3: Schedule with crosstalk awareness
        schedule = self.scheduler.schedule(placed_circuit)
        scheduled_circuit = self.scheduler.schedule_to_circuit(
            placed_circuit, schedule
        )

        # Step 4: Compute metrics
        metrics = self._compute_metrics(
            circuit, scheduled_circuit, schedule, mapping
        )

        return MitigationResult(
            original_circuit=circuit,
            mitigated_circuit=scheduled_circuit,
            qubit_mapping=mapping,
            schedule=schedule,
            metrics=metrics
        )

    def _apply_placement(
        self,
        circuit: QuantumCircuit,
        mapping: Dict[int, int]
    ) -> QuantumCircuit:
        """Apply qubit mapping to circuit."""
        # Create remapped circuit
        new_circuit = QuantumCircuit(
            circuit.num_qubits,
            circuit.num_clbits,
            name=circuit.name
        )

        # Copy metadata
        new_circuit.metadata = dict(circuit.metadata or {})
        new_circuit.metadata["qubit_mapping"] = mapping

        # Map each instruction
        for inst in circuit.data:
            op = inst.operation
            qargs = inst.qubits
            cargs = inst.clbits

            # Remap qubit arguments
            new_qargs = []
            for q in qargs:
                q_idx = q._index
                if q_idx in mapping:
                    mapped_phys = mapping[q_idx]
                    # Extract integer index from Qubit if needed
                    phys_idx = getattr(mapped_phys, '_index', mapped_phys) if not isinstance(mapped_phys, int) else mapped_phys
                    new_qargs.append(new_circuit.qubits[phys_idx])
                else:
                    new_qargs.append(q)

            new_circuit.append(op, new_qargs, cargs)

        return new_circuit

    def _compute_metrics(
        self,
        original: QuantumCircuit,
        mitigated: QuantumCircuit,
        schedule: List[List[int]],
        mapping: Dict[int, int]
    ) -> Dict[str, Any]:
        """Compute comparison metrics."""
        return {
            "original_depth": original.depth(),
            "original_two_qubit_gates": original.num_nonlocal_gates(),
            "mitigated_depth": mitigated.depth(),
            "mitigated_two_qubit_gates": mitigated.num_nonlocal_gates(),
            "schedule_layers": len(schedule),
            "qubit_mapping": mapping,
            "depth_change": mitigated.depth() - original.depth(),
            "depth_change_percent": (
                (mitigated.depth() - original.depth()) / max(original.depth(), 1) * 100
            ),
        }