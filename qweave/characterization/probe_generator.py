"""Generate probe circuits for crosstalk characterization."""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


@dataclass
class ProbeSpec:
    """Specification for a probe circuit."""
    name: str
    circuit: QuantumCircuit
    type: str  # 'individual_a', 'individual_b', 'concurrent'
    targets: Tuple[Tuple[int, ...], ...]


class ProbeGenerator:
    """Generate probe circuits for crosstalk characterization."""

    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.cx_error_rate = 0.001  # Baseline CNOT error for simulation

    def generate_probe_pair(
        self,
        op_a: Tuple[int, ...],
        op_b: Tuple[int, ...],
        gate_type: str = "cx"
    ) -> List[ProbeSpec]:
        """
        Generate three probe circuits for a pair of operations.

        Args:
            op_a: Qubits for first operation (control, target)
            op_b: Qubits for second operation (control, target)
            gate_type: Type of two-qubit gate ('cx' or 'cz')

        Returns:
            List of 3 ProbeSpec: A individual, B individual, AB concurrent
        """
        probes = []

        # Probe 1: A individually
        probes.append(self._create_individual_probe(op_a, "A", gate_type))

        # Probe 2: B individually
        probes.append(self._create_individual_probe(op_b, "B", gate_type))

        # Probe 3: A and B concurrently
        probes.append(self._create_concurrent_probe(op_a, op_b, gate_type))

        return probes

    def _create_individual_probe(
        self,
        qubits: Tuple[int, ...],
        label: str,
        gate_type: str
    ) -> ProbeSpec:
        """Create a single-operation probe."""
        n = max(qubits) + 1 if max(qubits) < self.num_qubits else self.num_qubits
        qr = QuantumRegister(n)
        cr = ClassicalRegister(n)
        qc = QuantumCircuit(qr, cr, name=f"probe_{label}_{qubits}")

        # Prepare Bell state on target qubits for fidelity measurement
        qc.h(qubits[0])
        if gate_type == "cx":
            qc.cx(qubits[0], qubits[1])
        elif gate_type == "cz":
            qc.cz(qubits[0], qubits[1])

        # Add inverse to return to |0...0>
        qc.cx(qubits[0], qubits[1]) if gate_type == "cx" else qc.cz(qubits[0], qubits[1])
        qc.h(qubits[0])

        qc.measure_all()

        return ProbeSpec(
            name=f"individual_{label}",
            circuit=qc,
            type=f"individual_{label.lower()}",
            targets=(qubits,)
        )

    def _create_concurrent_probe(
        self,
        op_a: Tuple[int, ...],
        op_b: Tuple[int, ...],
        gate_type: str
    ) -> ProbeSpec:
        """Create a concurrent-operation probe."""
        max_q = max(max(op_a), max(op_b))
        n = max_q + 1 if max_q < self.num_qubits else self.num_qubits

        qr = QuantumRegister(n)
        cr = ClassicalRegister(n)
        qc = QuantumCircuit(qr, cr, name=f"probe_concurrent_{op_a}_{op_b}")

        # Prepare both Bell states simultaneously (concurrent execution)
        qc.h(op_a[0])
        qc.h(op_b[0])

        if gate_type == "cx":
            qc.cx(op_a[0], op_a[1])
            qc.cx(op_b[0], op_b[1])
        elif gate_type == "cz":
            qc.cz(op_a[0], op_a[1])
            qc.cz(op_b[0], op_b[1])

        # Inverse operations
        if gate_type == "cx":
            qc.cx(op_a[0], op_a[1])
            qc.cx(op_b[0], op_b[1])
        else:
            qc.cz(op_a[0], op_a[1])
            qc.cz(op_b[0], op_b[1])

        qc.h(op_a[0])
        qc.h(op_b[0])

        qc.measure_all()

        return ProbeSpec(
            name="concurrent_AB",
            circuit=qc,
            type="concurrent",
            targets=(op_a, op_b)
        )

    def generate_all_probes(
        self,
        coupling_map: List[List[int]],
        max_distance: int = 2
    ) -> List[ProbeSpec]:
        """
        Generate probes for all candidate gate pairs within coupling map.

        Args:
            coupling_map: List of [control, target] pairs defining connectivity
            max_distance: Maximum hop distance between operations to consider

        Returns:
            List of all probe specifications
        """
        # Extract unique 2-qubit gates from coupling map
        import itertools

        base_gates = [tuple(sorted(pair)) for pair in coupling_map]
        base_gates = list(set(base_gates))  # Deduplicate

        probes = []
        for gate_a, gate_b in itertools.combinations(base_gates, 2):
            # Only consider gates within max_distance
            if self._gate_distance(gate_a, gate_b) <= max_distance:
                probes.extend(self.generate_probe_pair(gate_a, gate_b))

        return probes

    def _gate_distance(self, gate1: Tuple[int, ...], gate2: Tuple[int, ...]) -> int:
        """Calculate minimum distance between two gates' qubits."""
        qubits1 = set(gate1)
        qubits2 = set(gate2)

        if qubits1 & qubits2:  # Overlapping gates
            return 0

        # Simple distance metric: min distance between any qubit pair
        min_dist = float('inf')
        for q1 in qubits1:
            for q2 in qubits2:
                dist = abs(q1 - q2)
                min_dist = min(min_dist, dist)

        return int(min_dist)