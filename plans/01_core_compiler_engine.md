# Phase 1: Core Compiler Engine

## Objective
Implement the complete crosstalk-aware quantum compiler engine following the MEASURE → MODEL → MITIGATE pipeline. This is the central technical component of Q-Weave.

---

## Architecture Overview

```
qweave/
├── characterization/
│   ├── __init__.py
│   ├── probe_generator.py      # Generate individual/concurrent probe circuits
│   ├── executor.py              # Execute probes with Aer simulator
│   └── estimator.py             # Statistical interaction estimation
├── crosstalk_model/
│   ├── __init__.py
│   ├── matrix.py                # Interaction matrix representation
│   └── graph.py                 # NetworkX weighted interaction graph
├── mitigation/
│   ├── __init__.py
│   ├── cost_function.py         # Normalized cost function implementation
│   ├── placement.py             # 2-opt local search placement
│   └── scheduler.py             # Greedy crosstalk-aware scheduler
└── evaluation/
    ├── __init__.py
    ├── fidelity.py              # Hellinger fidelity (version-safe)
    └── metrics.py               # Circuit metrics computation
```

---

## Step 1: Environment Injector (Synthetic Crosstalk)

**File:** `qweave/characterization/environment_injector.py`

### Purpose
Inject synthetic correlated noise into circuits using DAG-based layer iteration with named custom instructions. This creates the controlled execution-dependent crosstalk environment for testing.

### Implementation

```python
"""Environment injector for synthetic crosstalk simulation."""

import itertools
from typing import Dict, Set, Tuple

from qiskit import QuantumCircuit
from qiskit.circuit import Instruction
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
```

---

## Step 2: Probe Generator

**File:** `qweave/characterization/probe_generator.py`

### Purpose
Generate individual and concurrent probe circuits for characterization.

### Implementation

```python
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
```

---

## Step 3: Profile Executor

**File:** `qweave/characterization/executor.py`

### Purpose
Execute probe circuits with specified noise model and shots.

### Implementation

```python
"""Probe circuit execution with Aer simulator."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel


@dataclass
class ExecutionResult:
    """Result from executing a single probe."""
    probe_name: str
    counts: Dict[str, int]
    shots: int
    fidelity: float
    standard_error: float
    seed: int


class ProbeExecutor:
    """Execute probe circuits with Aer simulator."""

    # Execution parameters from specification (Section 10 update)
    DEFAULT_SHOTS = 8192  # 8,192 shots per probe
    DEFAULT_SEED_REPEATS = 5  # 5 random seed repeats

    def __init__(self, simulator: Optional[AerSimulator] = None):
        self.simulator = simulator or AerSimulator()

    def execute_probe(
        self,
        probe_spec,
        noise_model: Optional[NoiseModel] = None,
        shots: int = DEFAULT_SHOTS,
        seed: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute a single probe circuit.

        Args:
            probe_spec: ProbeSpec containing the circuit
            noise_model: Optional noise model for simulation
            shots: Number of shots (default: 8192)
            seed: Random seed for reproducibility

        Returns:
            ExecutionResult with counts and fidelity metrics
        """
        if seed is not None:
            self.simulator.set_options(seed_simulator=seed)

        job = self.simulator.run(probe_spec.circuit, shots=shots, noise_model=noise_model)
        result = job.result()
        counts = result.get_counts()

        # Calculate fidelity (success probability of returning to |0...0>)
        ideal_outcome = "0" * probe_spec.circuit.num_clbits
        success_count = counts.get(ideal_outcome, 0)
        fidelity = success_count / shots
        standard_error = np.sqrt(fidelity * (1 - fidelity) / shots)

        return ExecutionResult(
            probe_name=probe_spec.name,
            counts=counts,
            shots=shots,
            fidelity=fidelity,
            standard_error=standard_error,
            seed=seed or 0
        )

    def execute_with_repeats(
        self,
        probe_spec,
        noise_model: Optional[NoiseModel] = None,
        shots: int = DEFAULT_SHOTS,
        repeats: int = DEFAULT_SEED_REPEATS
    ) -> Dict[str, Any]:
        """
        Execute probe with multiple seeds and return statistics.

        Returns:
            Dictionary with mean fidelity, standard error, and individual results
        """
        results = []

        for i in range(repeats):
            seed = 42 + i * 17  # Deterministic seed sequence
            result = self.execute_probe(probe_spec, noise_model, shots, seed)
            results.append(result)

        fidelities = [r.fidelity for r in results]
        mean_fidelity = np.mean(fidelities)
        # Standard error of the mean
        sem = np.std(fidelities, ddof=1) / np.sqrt(repeats) if repeats > 1 else results[0].standard_error

        return {
            "probe_name": probe_spec.name,
            "mean_fidelity": mean_fidelity,
            "standard_error": sem,
            "individual_results": results,
            "type": probe_spec.type,
            "targets": probe_spec.targets
        }

    def characterize_pair(
        self,
        probes: List[Any],  # List[ProbeSpec]
        noise_model: Optional[NoiseModel] = None
    ) -> Dict[str, Any]:
        """
        Characterize an operation pair with all three probe types.

        Args:
            probes: List of 3 ProbeSpec [A, B, concurrent]
            noise_model: Noise model for simulation

        Returns:
            Combined results for the operation pair
        """
        assert len(probes) == 3, "Expected 3 probes: A, B, and concurrent"

        results = {}
        for probe in probes:
            results[probe.type] = self.execute_with_repeats(probe, noise_model)

        return results
```

---

## Step 4: Interaction Estimator

**File:** `qweave/characterization/estimator.py`

### Purpose
Compute interaction scores from probe measurements using statistical significance gating.

### Implementation

```python
"""Statistical estimation of crosstalk interaction strengths."""

import math
from typing import Dict, Tuple, Any
import numpy as np


class InteractionEstimator:
    """
    Estimate crosstalk interaction strengths from probe measurements.

    Uses the exact statistical estimator from Specification Section 10:
        F_expect = F_A * F_B
        raw = max(0, F_expect - F_AB)
        SE = sqrt(F * (1-F) / shots) for each fidelity
        interaction = raw / F_expect if raw > 3*sqrt(SE_A^2 + SE_B^2 + SE_AB^2), else 0
    """

    SIGNIFICANCE_THRESHOLD = 3.0  # 3-sigma significance gate

    def estimate_interaction(
        self,
        f_a: float,      # Fidelity of operation A alone
        se_a: float,     # Standard error of F_A
        f_b: float,      # Fidelity of operation B alone
        se_b: float,     # Standard error of F_B
        f_ab: float,     # Fidelity of concurrent execution
        se_ab: float     # Standard error of F_AB
    ) -> Dict[str, float]:
        """
        Calculate interaction score between two operations.

        Args:
            f_a: Mean fidelity of operation A execution
            se_a: Standard error of F_A
            f_b: Mean fidelity of operation B execution
            se_b: Standard error of F_B
            f_ab: Mean fidelity of concurrent execution
            se_ab: Standard error of F_AB

        Returns:
            Dictionary containing:
                - expectation: F_A * F_B (expected independent fidelity)
                - raw_degradation: max(0, F_expect - F_AB)
                - combined_se: sqrt(SE_A^2 + SE_B^2 + SE_AB^2)
                - significance: raw_degradation / combined_se
                - interaction_score: normalized interaction (0 if not significant)
                - is_significant: boolean indicating if above threshold
        """
        # Expected fidelity if operations were independent
        f_expect = f_a * f_b

        # Raw degradation (execution-dependent error beyond independent errors)
        raw = max(0.0, f_expect - f_ab)

        # Combined standard error
        combined_se = math.sqrt(se_a**2 + se_b**2 + se_ab**2)

        # Significance ratio
        significance = raw / combined_se if combined_se > 0 else float('inf')

        # Apply significance gate
        is_significant = significance > self.SIGNIFICANCE_THRESHOLD

        if is_significant and f_expect > 0:
            interaction_score = raw / f_expect
        else:
            interaction_score = 0.0

        return {
            "expectation": f_expect,
            "raw_degradation": raw,
            "combined_se": combined_se,
            "significance": significance,
            "interaction_score": interaction_score,
            "is_significant": is_significant,
            "f_a": f_a,
            "f_b": f_b,
            "f_ab": f_ab
        }

    def estimate_from_probe_results(
        self,
        probe_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estimate interaction from full probe result dictionary.

        Args:
            probe_results: Output from ProbeExecutor.characterize_pair()
                         with keys: 'individual_a', 'individual_b', 'concurrent'

        Returns:
            Interaction estimate with metadata
        """
        if "individual_a" not in probe_results:
            # Handle direct probe structure
            return self._estimate_direct(probe_results)

        # Extract values from nested structure
        f_a = probe_results["individual_a"]["mean_fidelity"]
        se_a = probe_results["individual_a"]["standard_error"]
        f_b = probe_results["individual_b"]["mean_fidelity"]
        se_b = probe_results["individual_b"]["standard_error"]
        f_ab = probe_results["concurrent"]["mean_fidelity"]
        se_ab = probe_results["concurrent"]["standard_error"]

        estimate = self.estimate_interaction(f_a, se_a, f_b, se_b, f_ab, se_ab)

        # Add operation identifiers
        estimate["operation_a"] = probe_results["individual_a"].get("probe_name", "A")
        estimate["operation_b"] = probe_results["individual_b"].get("probe_name", "B")

        return estimate

    def _estimate_direct(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle flat result structure."""
        # Assume results has direct fidelity fields
        return self.estimate_interaction(
            results.get("f_a", 0.0),
            results.get("se_a", 0.01),
            results.get("f_b", 0.0),
            results.get("se_b", 0.01),
            results.get("f_ab", 0.0),
            results.get("se_ab", 0.01)
        )

    def build_interaction_matrix(
        self,
        all_probe_results: Dict[Any, Dict[str, Any]],
        gate_labels: list
    ) -> Tuple[np.ndarray, Dict[Tuple[int, int], Dict[str, Any]]]:
        """
        Build interaction matrix from all pairwise probe results.

        Args:
            all_probe_results: Mapping from gate pair to probe results
            gate_labels: List of gate identifiers in matrix order

        Returns:
            Tuple of (interaction_matrix, detailed_results_dict)
        """
        n = len(gate_labels)
        matrix = np.zeros((n, n))
        details = {}

        label_to_idx = {label: i for i, label in enumerate(gate_labels)}

        for (gate_a, gate_b), probe_results in all_probe_results.items():
            estimate = self.estimate_from_probe_results(probe_results)

            idx_a = label_to_idx.get(gate_a)
            idx_b = label_to_idx.get(gate_b)

            if idx_a is not None and idx_b is not None:
                matrix[idx_a, idx_b] = estimate["interaction_score"]
                matrix[idx_b, idx_a] = estimate["interaction_score"]
                details[(idx_a, idx_b)] = estimate

        return matrix, details
```

---

## Step 5: Interaction Matrix

**File:** `qweave/crosstalk_model/matrix.py`

```python
"""Interaction matrix representation and operations."""

from typing import Dict, List, Tuple, Optional
import numpy as np
import json


class InteractionMatrix:
    """Matrix representation of crosstalk interaction strengths."""

    def __init__(
        self,
        labels: List[Tuple[int, ...]],
        matrix: Optional[np.ndarray] = None
    ):
        """
        Initialize interaction matrix.

        Args:
            labels: List of gate labels (qubit tuples) for each row/column
            matrix: Optional pre-computed interaction matrix
        """
        self.labels = labels
        self.n = len(labels)
        self.matrix = matrix if matrix is not None else np.zeros((self.n, self.n))

    def get_interaction(self, i: int, j: int) -> float:
        """Get interaction strength between gates i and j."""
        return float(self.matrix[i, j])

    def set_interaction(self, i: int, j: int, value: float):
        """Set interaction strength between gates i and j."""
        self.matrix[i, j] = value
        self.matrix[j, i] = value  # Symmetric

    def get_strongest_interactions(self, threshold: float = 0.0) -> List[Tuple[int, int, float]]:
        """Get all interactions above threshold, sorted by strength."""
        interactions = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self.matrix[i, j] > threshold:
                    interactions.append((i, j, float(self.matrix[i, j])))

        return sorted(interactions, key=lambda x: x[2], reverse=True)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "labels": [list(label) for label in self.labels],
            "matrix": self.matrix.tolist()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "InteractionMatrix":
        """Create from dictionary."""
        labels = [tuple(label) for label in data["labels"]]
        matrix = np.array(data["matrix"])
        return cls(labels, matrix)

    def save(self, filepath: str):
        """Save to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "InteractionMatrix":
        """Load from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
```

---

## Step 6: Interaction Graph (NetworkX)

**File:** `qweave/crosstalk_model/graph.py`

```python
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
```

---

## Step 7: Cost Function

**File:** `qweave/mitigation/cost_function.py`

```python
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
```

---

## Step 8: Crosstalk-Aware Placement (2-Opt)

**File:** `qweave/mitigation/placement.py`

```python
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

            # Get physical assignments
            phys_a = mapping.get(node_a, node_a)
            phys_b = mapping.get(node_b, node_b)

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
```

---

## Step 9: Greedy Scheduler

**File:** `qweave/mitigation/scheduler.py`

```python
"""Crosstalk-aware greedy list scheduler."""

from typing import List, Dict, Set, Tuple, Optional
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from qiskit.circuit import DAGCircuit

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
```

---

## Step 10: Fidelity Estimator

**File:** `qweave/evaluation/fidelity.py`

```python
"""Version-safe Hellinger fidelity implementation."""

import math
from typing import Dict
import numpy as np


def hellinger_fidelity(
    counts_a: Dict[str, int],
    counts_b: Dict[str, int],
    shots_a: int = None,
    shots_b: int = None
) -> float:
    """
    Compute Hellinger fidelity between two distributions.

    This is a standalone, version-safe implementation that does not
    depend on Qiskit's experimental.measure module.

    Formula:
        F_H = (sum_i sqrt(p_i * q_i))^2

    Args:
        counts_a: First distribution counts
        counts_b: Second distribution counts
        shots_a: Total shots for distribution A
        shots_b: Total shots for distribution B

    Returns:
        Hellinger fidelity in [0, 1]

    Example:
        >>> counts_a = {"00": 8000, "11": 192}
        >>> counts_b = {"00": 4096, "11": 4096}
        >>> fidelity = hellinger_fidelity(counts_a, counts_b)
    """
    if shots_a is None:
        shots_a = sum(counts_a.values())
    if shots_b is None:
        shots_b = sum(counts_b.values())

    # Get all possible outcomes
    all_outcomes = set(counts_a.keys()) | set(counts_b.keys())

    # Compute Hellinger inner product
    h_sum = 0.0
    for outcome in all_outcomes:
        p = counts_a.get(outcome, 0) / shots_a
        q = counts_b.get(outcome, 0) / shots_b
        h_sum += math.sqrt(p * q)

    # Hellinger fidelity
    return h_sum ** 2


def compute_success_probability(
    counts: Dict[str, int],
    expected_outcome: str,
    shots: int = None
) -> float:
    """
    Compute success probability for a known expected outcome.

    Args:
        counts: Measurement counts
        expected_outcome: Expected bitstring
        shots: Total shots

    Returns:
        Probability of observing expected outcome
    """
    if shots is None:
        shots = sum(counts.values())

    success_count = counts.get(expected_outcome, 0)
    return success_count / shots


def compute_tvd(
    counts_a: Dict[str, int],
    counts_b: Dict[str, int],
    shots_a: int = None,
    shots_b: int = None
) -> float:
    """
    Compute Total Variation Distance between distributions.

    Args:
        counts_a: First distribution
        counts_b: Second distribution
        shots_a: Total shots for A
        shots_b: Total shots for B

    Returns:
        TVD in [0, 1]
    """
    if shots_a is None:
        shots_a = sum(counts_a.values())
    if shots_b is None:
        shots_b = sum(counts_b.values())

    all_outcomes = set(counts_a.keys()) | set(counts_b.keys())

    tvd = 0.0
    for outcome in all_outcomes:
        p = counts_a.get(outcome, 0) / shots_a
        q = counts_b.get(outcome, 0) / shots_b
        tvd += abs(p - q)

    return 0.5 * tvd
```

---

## Step 11: Integration - Mitigation Engine

**File:** `qweave/mitigation/engine.py`

```python
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
                if q._index in mapping:
                    new_idx = mapping[q._index]
                    new_qargs.append(new_circuit.qubits[new_idx])
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
```

---

## Phase 1 Completion Criteria

**This phase is complete when:**

1. All module files listed above are implemented and import successfully
2. `inject_crosstalk()` function correctly injects synthetic noise using DAG layers
3. `ProbeGenerator` creates valid probe circuits for given gate pairs
4. `InteractionEstimator` computes interaction scores using the exact statistical formula
5. `CrosstalkGraph` correctly represents interactions in NetworkX format
6. 2-opt placement reduces interaction cost from SabreLayout baseline
7. Greedy scheduler produces valid layer schedules with crosstalk awareness
8. `hellinger_fidelity()` is standalone and version-safe
9. `MitigationEngine` orchestrates the full pipeline

---

## Unit Test Checklist

Create tests for each module:

- [ ] `test_environment_injector.py`: Verify crosstalk injection produces correct noise model
- [ ] `test_probe_generator.py`: Verify probe circuits have correct structure
- [ ] `test_estimator.py`: Test interaction scoring with known values
- [ ] `test_graph.py`: Test graph construction and query methods
- [ ] `test_placement.py`: Test 2-opt reduces cost within 200 iterations
- [ ] `test_scheduler.py`: Test schedule respects dependencies
- [ ] `test_fidelity.py`: Test Hellinger fidelity against reference values

---

## Next Phase

Proceed to [02_validation_and_benchmarks.md](./02_validation_and_benchmarks.md) to implement Level 1 and Level 2 validation experiments.
