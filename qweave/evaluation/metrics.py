"""Circuit metrics computation for evaluation."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from qiskit import QuantumCircuit
from qiskit.circuit import Gate


@dataclass
class CircuitMetrics:
    """Metrics for a quantum circuit."""
    depth: int
    two_qubit_gates: int
    single_qubit_gates: int
    total_gates: int
    num_qubits: int
    coupling_usage: Dict[str, int]


class MetricsCalculator:
    """Compute various metrics for quantum circuits."""

    @staticmethod
    def compute_all_metrics(circuit: QuantumCircuit) -> CircuitMetrics:
        """
        Compute comprehensive metrics for a circuit.

        Args:
            circuit: Input quantum circuit

        Returns:
            CircuitMetrics dataclass with all metric values
        """
        # Count gate types
        two_qubit = 0
        single_qubit = 0
        total = len(circuit.data)
        coupling_usage = {}

        for inst in circuit.data:
            op = inst.operation

            if hasattr(op, 'num_qubits'):
                num_op_qubits = op.num_qubits if hasattr(op, 'num_qubits') else len(inst.qubits)
            else:
                num_op_qubits = len(inst.qubits)

            if num_op_qubits == 2:
                two_qubit += 1

                # Track coupling usage
                q0, q1 = sorted([q._index for q in inst.qubits[:2]])
                key = f"{q0}-{q1}"
                coupling_usage[key] = coupling_usage.get(key, 0) + 1
            elif num_op_qubits == 1:
                single_qubit += 1

        return CircuitMetrics(
            depth=circuit.depth(),
            two_qubit_gates=two_qubit,
            single_qubit_gates=single_qubit,
            total_gates=total,
            num_qubits=circuit.num_qubits,
            coupling_usage=coupling_usage
        )

    @staticmethod
    def get_two_qubit_gate_count(circuit: QuantumCircuit) -> int:
        """Count two-qubit gates in circuit."""
        count = 0
        for inst in circuit.data:
            if len(inst.qubits) == 2:
                count += 1
        return count

    @staticmethod
    def get_gate_depth_by_type(circuit: QuantumCircuit) -> Dict[str, int]:
        """Get depth for single-qubit and two-qubit gates separately."""
        from qiskit.converters import circuit_to_dag

        dag = circuit_to_dag(circuit)
        single_depth = 0
        two_qubit_depth = 0

        for node in dag.op_nodes():
            if len(node.qargs) == 1:
                single_depth = max(single_depth, node.layer)
            elif len(node.qargs) == 2:
                two_qubit_depth = max(two_qubit_depth, node.layer)

        return {
            "single_qubit_gates": single_depth + 1,
            "two_qubit_gates": two_qubit_depth + 1,
            "total": max(single_depth, two_qubit_depth) + 1
        }