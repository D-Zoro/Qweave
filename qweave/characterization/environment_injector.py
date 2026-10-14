"""Environment injector for synthetic crosstalk simulation."""

import itertools
from typing import Dict, Set, Tuple

from qiskit import QuantumCircuit
from qiskit.circuit import Instruction, Gate
from qiskit.converters import circuit_to_dag
from qiskit_aer.noise import NoiseModel, depolarizing_error


# Fixed noise tier table (Section 8 update)
NOISE_TIERS = {
    "HIGH": 0.15,
    "MEDIUM": 0.07,
    "LOW": 0.02,
}


def inject_crosstalk(
    qc: QuantumCircuit,
    hidden_rules: Dict[frozenset, float]
) -> Tuple[QuantumCircuit, NoiseModel]:
    """
    Inject synthetic crosstalk into a circuit based on hidden rules.

    Uses DAG layer iteration with standard add_quantum_error().
    Creates named custom instructions for correlated noise injection.

    Args:
        qc: Input quantum circuit
        hidden_rules: Mapping from frozenset of gate qubit pairs to error probability
                     Format: {frozenset({tuple(qubits_A), tuple(qubits_B)}): prob}

    Returns:
        Tuple of (modified circuit with injected gate markers, NoiseModel)

    Note:
        Only the environment-builder sees hidden_rules. Q-Weave's profiler
        must discover interactions empirically without access to these rules.

    Example:
        >>> qc = QuantumCircuit(4)
        >>> qc.cx(0, 1)
        >>> qc.cx(2, 3)
        >>> rules = {frozenset({(0, 1), (2, 3)}): 0.15}  # HIGH crosstalk
        >>> new_qc, noise_model = inject_crosstalk(qc, rules)
    """
    dag = circuit_to_dag(qc)
    new_qc = qc.copy_empty_like()

    # Track injected gate names for noise model
    injected_names: Dict[str, Tuple[Tuple[int, ...], float]] = {}

    for layer in dag.layers():
        nodes = list(layer["graph"].op_nodes())

        # Add all gates in this layer to the new circuit
        for node in nodes:
            new_qc.append(node.op, node.qargs, node.cargs)

        # Check for concurrent interactions that match hidden rules
        for node_a, node_b in itertools.combinations(nodes, 2):
            qa = tuple(q._index for q in node_a.qargs)
            qb = tuple(q._index for q in node_b.qargs)

            key = frozenset([qa, qb])
            if key in hidden_rules:
                # Create combined qubit tuple for the correlated error gate
                combined = tuple(sorted(set(qa) | set(qb)))

                # Create unique gate name for this interaction
                name = f"xtalk_{'_'.join(map(str, combined))}_{node_a.name}_{node_b.name}"
                injected_names[name] = (combined, hidden_rules[key])

                # Insert marker instruction (no-op, just for noise attachment)
                new_qc.append(
                    Instruction(name, len(combined), 0, []),
                    combined
                )

    # Build noise model with correlated errors for each injected marker
    noise_model = NoiseModel()
    for name, (qubits, prob) in injected_names.items():
        error = depolarizing_error(prob, len(qubits))
        noise_model.add_quantum_error(error, name, qubits)

    return new_qc, noise_model


def create_synthetic_environment(
    num_qubits: int,
    tier: str = "HIGH"
) -> Dict[frozenset, float]:
    """
    Create a synthetic crosstalk environment with random interactions.

    Args:
        num_qubits: Number of qubits in the system
        tier: Noise tier (HIGH, MEDIUM, LOW)

    Returns:
        Hidden rules dictionary for inject_crosstalk()
    """
    import random

    prob = NOISE_TIERS.get(tier, 0.07)
    rules = {}

    # Create a few random crosstalk pairs
    # In practice, these represent physically proximate operations
    for _ in range(num_qubits // 4):
        q1 = random.randint(0, num_qubits - 2)
        q2 = random.randint(0, num_qubits - 2)

        if q1 != q2:
            pair1 = (q1, q1 + 1)
            pair2 = (q2, q2 + 1)
            key = frozenset([pair1, pair2])
            rules[key] = prob

    return rules