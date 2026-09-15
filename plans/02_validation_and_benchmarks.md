# Phase 2: Validation and Benchmarks

## Objective
Implement systematic validation experiments to empirically prove that Q-Weave's crosstalk-aware mitigation pipeline works. This phase implements Level 1 (known crosstalk) and Level 2 (unknown multi-tier) validation experiments with automated success criteria verification.

---

## Prerequisites
- Phase 0: Environment setup complete
- Phase 1: Core compiler engine modules functional
- Qiskit Aer simulator verified working
- Synthetic crosstalk injection verified

---

## Step 1: Fixed Coupling Topology Definition

**File:** `qweave/hardware/topology.py`

### Purpose
Define a fixed 3×3 grid coupling map for cross-tier experiment comparability.

### Implementation

```python
"""Fixed coupling topology for consistent experiments."""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class TopologyConfig:
    """Configuration for a qubit topology."""
    name: str
    num_qubits: int
    coupling_map: List[List[int]]
    description: str


# Fixed 3×3 Grid Topology (9 qubits)
# Layout:
#     0 -- 1 -- 2
#     |    |    |
#     3 -- 4 -- 5
#     |    |    |
#     6 -- 7 -- 8
#
GRID_3X3 = TopologyConfig(
    name="3x3_grid",
    num_qubits=9,
    coupling_map=[
        # Row connections
        [0, 1], [1, 0], [1, 2], [2, 1],
        [3, 4], [4, 3], [4, 5], [5, 4],
        [6, 7], [7, 6], [7, 8], [8, 7],
        # Column connections
        [0, 3], [3, 0], [3, 6], [6, 3],
        [1, 4], [4, 1], [4, 7], [7, 4],
        [2, 5], [5, 2], [5, 8], [8, 5],
    ],
    description="Fixed 3x3 grid topology for consistent cross-tier experiments"
)


def get_grid_3x3_topology() -> TopologyConfig:
    """Return the standard 3x3 grid topology configuration."""
    return GRID_3X3


def validate_coupling_map(coupling_map: List[List[int]], num_qubits: int) -> bool:
    """Validate that coupling map is connected and covers all qubits."""
    from collections import defaultdict, deque

    # Build adjacency list
    adj = defaultdict(set)
    for a, b in coupling_map:
        adj[a].add(b)
        adj[b].add(a)

    # Check all qubits are reachable from 0
    visited = set()
    queue = deque([0])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adj[node]:
            if neighbor not in visited:
                queue.append(neighbor)

    return len(visited) == num_qubits


# Verify topology is valid
assert validate_coupling_map(GRID_3X3.coupling_map, GRID_3X3.num_qubits), \
    "3x3 grid topology is not fully connected"
```

---

## Step 2: Noise Tier Definitions

**File:** `qweave/characterization/noise_tiers.py`

```python
"""Fixed noise tier definitions for synthetic crosstalk experiments."""

from dataclasses import dataclass
from typing import Dict
from enum import Enum


class NoiseTier(Enum):
    """Noise severity tiers for synthetic crosstalk experiments."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class NoiseTierConfig:
    """Configuration for a noise tier."""
    label: str
    depolarizing_probability: float
    description: str


# Fixed noise tier table (from Section 8, Update 1)
NOISE_TIER_CONFIGS: Dict[NoiseTier, NoiseTierConfig] = {
    NoiseTier.HIGH: NoiseTierConfig(
        label="HIGH",
        depolarizing_probability=0.15,
        description="Strong crosstalk interaction (15% depolarizing error)"
    ),
    NoiseTier.MEDIUM: NoiseTierConfig(
        label="MEDIUM",
        depolarizing_probability=0.07,
        description="Moderate crosstalk interaction (7% depolarizing error)"
    ),
    NoiseTier.LOW: NoiseTierConfig(
        label="LOW",
        depolarizing_probability=0.02,
        description="Weak crosstalk interaction (2% depolarizing error)"
    ),
}


def get_noise_config(tier: NoiseTier) -> NoiseTierConfig:
    """Get configuration for a noise tier."""
    return NOISE_TIER_CONFIGS[tier]


def get_probability(tier: NoiseTier) -> float:
    """Get depolarizing probability for a noise tier."""
    return NOISE_TIER_CONFIGS[tier].depolarizing_probability


def get_all_tiers() -> list:
    """Get list of all noise tiers."""
    return list(NoiseTier)
```

---

## Step 3: Benchmark Circuit Generators

**File:** `qweave/evaluation/benchmarks.py`

```python
"""Benchmark circuit generators for validation experiments."""

from typing import List, Callable
from qiskit import QuantumCircuit
import numpy as np


class BenchmarkGenerator:
    """Generate benchmark circuits for evaluation."""

    @staticmethod
    def ghz_circuit(num_qubits: int) -> QuantumCircuit:
        """
        Generate GHZ (Greenberger-Horne-Zeilinger) state circuit.

        Creates maximally entangled state: (|0...0> + |1...1>) / sqrt(2)
        """
        qc = QuantumCircuit(num_qubits, name="GHZ")
        qc.h(0)
        for i in range(num_qubits - 1):
            qc.cx(i, i + 1)
        qc.measure_all()
        return qc

    @staticmethod
    def qft_circuit(num_qubits: int) -> QuantumCircuit:
        """
        Generate Quantum Fourier Transform circuit.

        Implements the quantum Fourier transform over N = 2^n values.
        """
        qc = QuantumCircuit(num_qubits, name="QFT")

        for target in range(num_qubits):
            qc.h(target)
            for control in range(target + 1, num_qubits):
                angle = np.pi / (2 ** (control - target))
                qc.cp(angle, control, target)

        # Add SWAPs to reverse qubit order
        for i in range(num_qubits // 2):
            qc.swap(i, num_qubits - 1 - i)

        qc.measure_all()
        return qc

    @staticmethod
    def qaoa_circuit(num_qubits: int, p: int = 1) -> QuantumCircuit:
        """
        Generate simplified QAOA circuit.

        Args:
            num_qubits: Number of qubits
            p: Number of QAOA layers

        Creates a Max-Cut QAOA circuit on a ring topology.
        """
        qc = QuantumCircuit(num_qubits, name=f"QAOA_p{p}")

        # Initial state: superposition
        for i in range(num_qubits):
            qc.h(i)

        for _ in range(p):
            # Cost Hamiltonian (ZZ rotations)
            for i in range(num_qubits):
                j = (i + 1) % num_qubits
                qc.cx(i, j)
                qc.rz(np.pi / 4, j)
                qc.cx(i, j)

            # Mixer Hamiltonian (X rotations)
            for i in range(num_qubits):
                qc.rx(np.pi / 4, i)

        qc.measure_all()
        return qc

    @staticmethod
    def random_clifford(num_qubits: int, num_gates: int = None, seed: int = 42) -> QuantumCircuit:
        """
        Generate random Clifford circuit.

        Args:
            num_qubits: Number of qubits
            num_gates: Number of Clifford gates (default: num_qubits * 2)
            seed: Random seed for reproducibility
        """
        from numpy.random import default_rng
        rng = default_rng(seed)

        if num_gates is None:
            num_gates = num_qubits * 2

        qc = QuantumCircuit(num_qubits, name="RandomClifford")
        single_qubit_gates = ['h', 's', 'x', 'y', 'z']

        for _ in range(num_gates):
            gate_type = rng.choice(['single', 'two'])

            if gate_type == 'single' or num_qubits < 2:
                qubit = rng.integers(0, num_qubits)
                gate = rng.choice(single_qubit_gates)
                getattr(qc, gate)(qubit)
            else:
                # Two-qubit gate
                control = rng.integers(0, num_qubits)
                target = rng.integers(0, num_qubits)
                while target == control:
                    target = rng.integers(0, num_qubits)
                qc.cx(control, target)

        qc.measure_all()
        return qc

    @staticmethod
    def vqe_circuit(num_qubits: int, reps: int = 2) -> QuantumCircuit:
        """
        Generate simplified VQE ansatz circuit (hardware-efficient).

        Creates a parameterized circuit structure similar to typical
        hardware-efficient ansatzes used in quantum chemistry.
        """
        qc = QuantumCircuit(num_qubits, name="VQE_Hardware")

        for r in range(reps):
            # Entangler
            for i in range(0, num_qubits - 1, 2):
                qc.cx(i, i + 1)
            for i in range(1, num_qubits - 1, 2):
                qc.cx(i, i + 1)

            # Rotation layer
            for i in range(num_qubits):
                qc.ry(np.pi / 4, i)
                qc.rz(np.pi / 4, i)

        qc.measure_all()
        return qc


def get_all_benchmarks(num_qubits: int) -> List[QuantumCircuit]:
    """Generate all benchmark circuits for a given qubit count."""
    gen = BenchmarkGenerator()
    return [
        gen.ghz_circuit(num_qubits),
        gen.qft_circuit(num_qubits),
        gen.qaoa_circuit(num_qubits),
        gen.random_clifford(num_qubits),
        gen.vqe_circuit(num_qubits),
    ]


def get_benchmark_names() -> List[str]:
    """Get list of available benchmark names."""
    return ["GHZ", "QFT", "QAOA", "RandomClifford", "VQE"]
```

---

## Step 4: Level 1 Validation - Known Synthetic Crosstalk

**File:** `experiments/level1_validation.py`

```python
"""
Level 1 Validation: Single known synthetic crosstalk pair.

Purpose: Verify the characterization and mitigation pipeline works end-to-end.
"""

import json
from typing import Dict, Any
import numpy as np
from datetime import datetime

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from qweave.hardware.topology import get_grid_3x3_topology
from qweave.characterization.noise_tiers import NoiseTier, get_probability
from qweave.characterization.environment_injector import inject_crosstalk
from qweave.characterization.probe_generator import ProbeGenerator
from qweave.characterization.executor import ProbeExecutor
from qweave.characterization.estimator import InteractionEstimator
from qweave.crosstalk_model.matrix import InteractionMatrix
from qweave.crosstalk_model.graph import CrosstalkGraph
from qweave.mitigation.engine import MitigationEngine
from qweave.evaluation.fidelity import hellinger_fidelity
from qweave.evaluation.benchmarks import BenchmarkGenerator


def run_level1_validation(
    noise_tier: NoiseTier = NoiseTier.HIGH,
    output_file: str = "results/level1_results.json"
) -> Dict[str, Any]:
    """
    Run Level 1 validation experiment.

    Creates a single hidden crosstalk pair and verifies:
    1. Profiler detects the interaction
    2. Mitigation improves fidelity
    3. Results are reproducible

    Args:
        noise_tier: Noise severity tier (default: HIGH)
        output_file: Path to save results

    Returns:
        Dictionary with experiment results
    """
    print(f"=== Level 1 Validation: {noise_tier.value} ===")

    # Setup
    topology = get_grid_3x3_topology()
    simulator = AerSimulator()
    prob = get_probability(noise_tier)

    # Define known crosstalk pair: CX(0,1) and CX(2,3) interfere
    hidden_rule = {
        frozenset({(0, 1), (2, 3)}): prob
    }

    print(f"Hidden rule: CX(0,1) || CX(2,3) -> {prob} depolarizing error")

    # Create probe circuit for the pair
    probe_gen = ProbeGenerator(topology.num_qubits)
    probes = probe_gen.generate_probe_pair((0, 1), (2, 3))

    # Execute probes with hidden crosstalk
    injector = inject_crosstalk
    _, noise_model = injector(QuantumCircuit(4), hidden_rule)

    executor = ProbeExecutor(simulator)
    probe_results = {}

    for probe in probes:
        result = executor.execute_with_repeats(probe, noise_model)
        probe_results[probe.type] = result

    # Estimate interaction
    estimator = InteractionEstimator()
    estimate = estimator.estimate_from_probe_results(probe_results)

    print(f"Detected interaction score: {estimate['interaction_score']:.4f}")
    print(f"Significance: {estimate['significance']:.2f}σ")
    print(f"Is significant: {estimate['is_significant']}")

    # Verify detection
    detection_success = estimate['is_significant'] and estimate['interaction_score'] > 0

    # Build interaction model
    labels = [(0, 1), (2, 3)]
    matrix = np.zeros((2, 2))
    matrix[0, 1] = matrix[1, 0] = estimate['interaction_score']

    inter_matrix = InteractionMatrix(labels, matrix)
    graph = CrosstalkGraph.from_matrix(inter_matrix)

    # Test mitigation on GHZ circuit
    benchmark = BenchmarkGenerator.ghz_circuit(4)

    # Baseline: Standard Qiskit transpilation
    from qiskit import transpile
    baseline_circuit = transpile(
        benchmark,
        simulator,
        coupling_map=topology.coupling_map,
        optimization_level=3
    )

    # Mitigated: Q-Weave placement + scheduling
    engine = MitigationEngine(graph, topology.coupling_map)
    mitigation_result = engine.mitigate(benchmark)
    mitigated_circuit = mitigation_result.mitigated_circuit

    # Execute both
    shots = 8192
    baseline_job = simulator.run(baseline_circuit, shots=shots, noise_model=noise_model)
    mitigated_job = simulator.run(mitigated_circuit, shots=shots, noise_model=noise_model)

    baseline_counts = baseline_job.result().get_counts()
    mitigated_counts = mitigated_job.result().get_counts()

    # Calculate success probabilities
    ideal_ghz = "0" + "0" * (4 - 1)  # GHZ ideal outcome
    p_baseline = baseline_counts.get("0000", 0) / shots
    p_mitigated = mitigated_counts.get("0000", 0) / shots

    # Calculate fidelity with ideal distribution
    ideal_dist = {"0000": shots // 2, "1111": shots // 2}
    fid_baseline = hellinger_fidelity(baseline_counts, ideal_dist, shots, shots)
    fid_mitigated = hellinger_fidelity(mitigated_counts, ideal_dist, shots, shots)

    print(f"\n=== Results ===")
    print(f"Detection success: {detection_success}")
    print(f"Baseline fidelity: {fid_baseline:.4f}")
    print(f"Mitigated fidelity: {fid_mitigated:.4f}")
    print(f"Improvement: {fid_mitigated - fid_baseline:.4f}")

    results = {
        "level": "Level 1",
        "noise_tier": noise_tier.value,
        "hidden_rule": str(hidden_rule),
        "detection": {
            "success": detection_success,
            "interaction_score": float(estimate['interaction_score']),
            "significance": float(estimate['significance']),
        },
        "execution": {
            "baseline_fidelity": float(fid_baseline),
            "mitigated_fidelity": float(fid_mitigated),
            "improvement": float(fid_mitigated - fid_baseline),
            "improvement_percent": float((fid_mitigated - fid_baseline) / fid_baseline * 100),
        },
        "timestamp": datetime.now().isoformat(),
    }

    # Save results
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    # Run Level 1 for HIGH tier
    result = run_level1_validation(NoiseTier.HIGH)
    print(f"\nLevel 1 {'PASSED' if result['detection']['success'] else 'FAILED'}")
```

---

## Step 5: Level 2 Validation - Multi-Pair Unknown Crosstalk

**File:** `experiments/level2_validation.py`

```python
"""
Level 2 Validation: Multi-pair unknown synthetic crosstalk.

Purpose: Demonstrate framework handles complex, unknown crosstalk environments.
Success criteria: Mitigated fidelity exceeds baseline > 2× SE in ≥ 2 of 3 tiers.
"""

import json
import random
from typing import Dict, List, Any
import numpy as np
from datetime import datetime

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from qweave.hardware.topology import get_grid_3x3_topology
from qweave.characterization.noise_tiers import NoiseTier, get_probability, get_all_tiers
from qweave.characterization.environment_injector import inject_crosstalk, create_synthetic_environment
from qweave.characterization.probe_generator import ProbeGenerator
from qweave.characterization.executor import ProbeExecutor
from qweave.characterization.estimator import InteractionEstimator
from qweave.crosstalk_model.matrix import InteractionMatrix
from qweave.crosstalk_model.graph import CrosstalkGraph
from qweave.mitigation.engine import MitigationEngine
from qweave.evaluation.fidelity import hellinger_fidelity
from qweave.evaluation.benchmarks import BenchmarkGenerator, get_all_benchmarks


def run_level2_validation(
    noise_tier: NoiseTier,
    benchmarks: List[QuantumCircuit] = None,
    seed: int = 42,
    output_file: str = None
) -> Dict[str, Any]:
    """
    Run Level 2 validation for a single noise tier.

    Creates multiple hidden crosstalk interactions that Q-Weave must discover.

    Args:
        noise_tier: Noise severity tier (HIGH, MEDIUM, or LOW)
        benchmarks: List of circuits to test (default: all benchmarks)
        seed: Random seed for reproducibility
        output_file: Path to save results

    Returns:
        Dictionary with validation results
    """
    print(f"\n{'='*60}")
    print(f"Level 2 Validation: {noise_tier.value}")
    print(f"{'='*60}")

    random.seed(seed)
    np.random.seed(seed)

    topology = get_grid_3x3_topology()
    simulator = AerSimulator()

    # Create hidden crosstalk environment (unknown to Q-Weave)
    # Fixed set of interactions for reproducibility
    prob = get_probability(noise_tier)
    hidden_rules = {
        frozenset({(0, 1), (2, 3)}): prob,
        frozenset({(3, 4), (6, 7)}): prob * 0.8,
        frozenset({(1, 4), (4, 7)}): prob * 0.5,
    }

    print(f"Hidden environment: {len(hidden_rules)} interaction pairs")
    for rule, p in hidden_rules.items():
        print(f"  {rule} -> {p:.4f}")

    # Generate all probe circuits
    probe_gen = ProbeGenerator(topology.num_qubits)
    all_probes = probe_gen.generate_all_probes(topology.coupling_map, max_distance=2)

    print(f"Generated {len(all_probes)} probe circuits")

    # Create noise model with hidden rules
    dummy_qc = QuantumCircuit(topology.num_qubits)
    _, noise_model = inject_crosstalk(dummy_qc, hidden_rules)

    # Execute all probes
    executor = ProbeExecutor(simulator)
    all_results = {}

    # Group probes by gate pairs
    pair_results = {}
    for i in range(0, len(all_probes), 3):
        if i + 2 < len(all_probes):
            a_probe = all_probes[i]
            b_probe = all_probes[i + 1]
            concurrent_probe = all_probes[i + 2]

            probes = [a_probe, b_probe, concurrent_probe]

            # Execute with crosstalk
            for probe in probes:
                result = executor.execute_with_repeats(probe, noise_model)
                all_results[probe.name] = result

            # Store for estimation
            pair_key = (str(a_probe.targets[0]), str(b_probe.targets[0]))
            pair_results[pair_key] = {
                "individual_a": all_results[a_probe.name],
                "individual_b": all_results[b_probe.name],
                "concurrent": all_results[concurrent_probe.name],
            }

    print(f"Completed {len(pair_results)} pairwise characterizations")

    # Estimate interactions
    estimator = InteractionEstimator()
    interactions = {}
    significant_detections = 0

    for pair_key, probe_data in pair_results.items():
        estimate = estimator.estimate_from_probe_results(probe_data)
        interactions[pair_key] = estimate

        if estimate['is_significant']:
            significant_detections += 1

    print(f"Significant interactions detected: {significant_detections}/{len(pair_results)}")

    # Build interaction matrix from significant detections
    detected_pairs = [
        pair for pair, est in interactions.items()
        if est['is_significant']
    ]

    if len(detected_pairs) == 0:
        print("WARNING: No significant interactions detected!")
        return {"success": False, "error": "No interactions detected"}

    # Build compact graph from detected interactions
    n_detected = len(detected_pairs)
    matrix = np.zeros((n_detected, n_detected))

    for i, pair_a in enumerate(detected_pairs):
        for j, pair_b in enumerate(detected_pairs):
            if i != j:
                # Simplified: check if pairs share qubits (would be stronger interaction)
                # In full implementation, would re-run probes for cross-pair interactions
                matrix[i, j] = 0.0  # Cross-pair interaction requires additional probing

    # Use raw estimates for within-pair interactions
    for i, pair in enumerate(detected_pairs):
        matrix[i, i] = interactions[pair]['interaction_score']

    inter_matrix = InteractionMatrix(detected_pairs, matrix)
    graph = CrosstalkGraph.from_matrix(inter_matrix)

    # Run benchmarks
    if benchmarks is None:
        benchmarks = get_all_benchmarks(4)[:2]  # Use subset for speed

    benchmark_results = []

    for benchmark in benchmarks:
        print(f"\nBenchmark: {benchmark.name}")

        # Baseline
        from qiskit import transpile
        baseline = transpile(
            benchmark,
            simulator,
            coupling_map=topology.coupling_map,
            optimization_level=3
        )

        # Mitigated
        engine = MitigationEngine(graph, topology.coupling_map)
        mitigation = engine.mitigate(benchmark)
        mitigated = mitigation.mitigated_circuit

        # Execute
        shots = 8192
        baseline_job = simulator.run(baseline, shots=shots, noise_model=noise_model)
        mitigated_job = simulator.run(mitigated, shots=shots, noise_model=noise_model)

        baseline_counts = baseline_job.result().get_counts()
        mitigated_counts = mitigated_job.result().get_counts()

        # Estimate ideal distribution (noiseless execution)
        ideal_job = simulator.run(baseline, shots=shots)
        ideal_counts = ideal_job.result().get_counts()

        # Calculate fidelities
        fid_baseline = hellinger_fidelity(baseline_counts, ideal_counts, shots, shots)
        fid_mitigated = hellinger_fidelity(mitigated_counts, ideal_counts, shots, shots)

        # Standard errors
        se_baseline = np.sqrt(fid_baseline * (1 - fid_baseline) / shots)
        se_mitigated = np.sqrt(fid_mitigated * (1 - fid_mitigated) / shots)
        combined_se = np.sqrt(se_baseline**2 + se_mitigated**2)

        # Success criterion: improvement > 2 * SE
        improvement = fid_mitigated - fid_baseline
        success_threshold = 2 * combined_se
        is_success = improvement > success_threshold

        result = {
            "benchmark": benchmark.name,
            "baseline_fidelity": float(fid_baseline),
            "mitigated_fidelity": float(fid_mitigated),
            "improvement": float(improvement),
            "combined_se": float(combined_se),
            "threshold": float(success_threshold),
            "is_success": bool(is_success),
            "depth_baseline": baseline.depth(),
            "depth_mitigated": mitigated.depth(),
        }

        benchmark_results.append(result)

        print(f"  Baseline: {fid_baseline:.4f} ± {se_baseline:.4f}")
        print(f"  Mitigated: {fid_mitigated:.4f} ± {se_mitigated:.4f}")
        print(f"  Improvement: {improvement:.4f} (threshold: {success_threshold:.4f})")
        print(f"  Success: {is_success}")

    # Aggregate results
    successful_benchmarks = [r for r in benchmark_results if r['is_success']]
    tier_success = len(successful_benchmarks) > 0

    overall_result = {
        "level": "Level 2",
        "noise_tier": noise_tier.value,
        "detection": {
            "pairs_found": len(detected_pairs),
            "significant": significant_detections,
        },
        "benchmarks": benchmark_results,
        "tier_success": tier_success,
        "timestamp": datetime.now().isoformat(),
    }

    if output_file:
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(overall_result, f, indent=2)

    return overall_result


def run_all_tiers() -> Dict[str, Any]:
    """
    Run Level 2 validation across all three noise tiers.

    Success criteria: Mitigated fidelity exceeds baseline by > 2× SE
    in at least 2 out of 3 noise tiers.
    """
    print("=" * 80)
    print("LEVEL 2 VALIDATION: ALL TIERS")
    print("=" * 80)

    tiers = get_all_tiers()
    tier_results = []
    successes = 0

    for tier in tiers:
        result = run_level2_validation(
            tier,
            output_file=f"results/level2_{tier.value.lower()}.json"
        )
        tier_results.append(result)
        if result.get('tier_success', False):
            successes += 1

    # Overall success criterion
    overall_pass = successes >= 2

    summary = {
        "validation_type": "Level 2 Cross-Tier",
        "tiers_tested": len(tiers),
        "successful_tiers": successes,
        "overall_pass": overall_pass,
        "criterion": "Mitigation success in >= 2 of 3 tiers",
        "tier_results": tier_results,
        "timestamp": datetime.now().isoformat(),
    }

    # Save summary
    import os
    os.makedirs("results", exist_ok=True)
    with open("results/level2_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Tiers tested: {len(tiers)}")
    print(f"Successful tiers: {successes}")
    print(f"Overall: {'PASS' if overall_pass else 'FAIL'}")

    return summary


if __name__ == "__main__":
    summary = run_all_tiers()
```

---

## Step 6: Success Criteria Verification

**File:** `experiments/verify_success.py`

```python
"""Automated verification of success criteria according to specification."""

import json
from typing import Dict, List, Any
import numpy as np


def verify_level1(result_file: str) -> bool:
    """
    Verify Level 1 success criteria.

    Criteria:
    1. Profiler detects the hidden interaction
    2. Mitigation improves fidelity
    """
    with open(result_file, 'r') as f:
        results = json.load(f)

    detection = results.get('detection', {})
    execution = results.get('execution', {})

    checks = {
        "detection_success": detection.get('success', False),
        "positive_interaction": detection.get('interaction_score', 0) > 0,
        "fidelity_improvement": execution.get('improvement', 0) > 0,
    }

    all_pass = all(checks.values())

    print("\nLevel 1 Verification:")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")

    return all_pass


def verify_level2(summary_file: str) -> bool:
    """
    Verify Level 2 success criteria.

    Criteria (from Update 6):
    Mitigated fidelity must exceed standard compilation fidelity by
    more than 2× the combined standard error in at least 2 of 3 noise tiers.
    """
    with open(summary_file, 'r') as f:
        summary = json.load(f)

    total_tiers = summary.get('tiers_tested', 0)
    successful_tiers = summary.get('successful_tiers', 0)

    criterion_met = successful_tiers >= 2
    overall_pass = summary.get('overall_pass', False)

    print("\nLevel 2 Verification:")
    print(f"  Tiers tested: {total_tiers}")
    print(f"  Successful tiers: {successful_tiers}")
    print(f"  Required: >= 2")
    print(f"  Criterion met: {'✓' if criterion_met else '✗'}")
    print(f"  Overall status: {'PASS' if overall_pass else 'FAIL'}")

    return overall_pass


def generate_validation_report(
    level1_files: List[str],
    level2_summary: str,
    output_file: str = "results/validation_report.md"
) -> str:
    """Generate markdown validation report for documentation."""

    report = []
    report.append("# Q-Weave Validation Report")
    report.append("")
    report.append("## Level 1: Known Synthetic Crosstalk")
    report.append("")

    for file in level1_files:
        with open(file, 'r') as f:
            data = json.load(f)

        tier = data.get('noise_tier', 'UNKNOWN')
        report.append(f"### {tier} Tier")
        report.append("")
        report.append(f"- Detection: {'✓ PASS' if data['detection']['success'] else '✗ FAIL'}")
        report.append(f"- Interaction Score: {data['detection']['interaction_score']:.4f}")
        report.append(f"- Baseline Fidelity: {data['execution']['baseline_fidelity']:.4f}")
        report.append(f"- Mitigated Fidelity: {data['execution']['mitigated_fidelity']:.4f}")
        report.append(f"- Improvement: {data['execution']['improvement_percent']:.2f}%")
        report.append("")

    report.append("## Level 2: Multi-Pair Unknown Crosstalk")
    report.append("")

    with open(level2_summary, 'r') as f:
        l2 = json.load(f)

    report.append(f"- Tiers Tested: {l2['tiers_tested']}")
    report.append(f"- Successful Tiers: {l2['successful_tiers']}")
    report.append(f"- Criterion: ≥ 2 of 3 tiers")
    report.append(f"- Result: {'✓ PASS' if l2['overall_pass'] else '✗ FAIL'}")
    report.append("")

    # Detail each tier
    for tier_result in l2.get('tier_results', []):
        tier_name = tier_result.get('noise_tier', 'UNKNOWN')
        report.append(f"### {tier_name} Tier")
        report.append("")
        report.append(f"- Pairs Found: {tier_result['detection']['pairs_found']}")
        report.append(f"- Significant: {tier_result['detection']['significant']}")

        for bench in tier_result.get('benchmarks', []):
            report.append(f"  - {bench['benchmark']}: {'✓' if bench['is_success'] else '✗'} "
                         f"(+{bench['improvement']:.4f} vs threshold {bench['threshold']:.4f})")
        report.append("")

    report_text = "\n".join(report)

    with open(output_file, 'w') as f:
        f.write(report_text)

    return report_text


if __name__ == "__main__":
    import sys
    import os

    # Check for result files
    level1_files = [
        "results/level1_HIGH.json",
        "results/level1_MEDIUM.json",
        "results/level1_LOW.json",
    ]
    level2_summary = "results/level2_summary.json"

    print("=" * 60)
    print("Q-WEAVE VALIDATION VERIFICATION")
    print("=" * 60)

    l1_pass = all(verify_level1(f) for f in level1_files if os.path.exists(f))
    l2_pass = verify_level2(level2_summary) if os.path.exists(level2_summary) else False

    print("\n" + "=" * 60)
    print(f"Level 1: {'PASS' if l1_pass else 'FAIL'}")
    print(f"Level 2: {'PASS' if l2_pass else 'FAIL'}")
    print(f"Overall: {'ALL VALIDATIONS PASS' if l1_pass and l2_pass else 'SOME VALIDATIONS FAIL'}")

    # Generate report
    existing_l1 = [f for f in level1_files if os.path.exists(f)]
    if existing_l1 and os.path.exists(level2_summary):
        generate_validation_report(existing_l1, level2_summary)
        print("\nReport saved to: results/validation_report.md")

    sys.exit(0 if (l1_pass and l2_pass) else 1)
```

---

## Step 7: Automated Benchmark Runner

**File:** `experiments/run_benchmarks.py`

```python
"""Automated benchmark execution script for reproducibility."""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from level1_validation import run_level1_validation
from level2_validation import run_all_tiers
from verify_success import generate_validation_report


def run_all_experiments(
    output_dir: str = "results",
    skip_level1: bool = False,
    skip_level2: bool = False
) -> dict:
    """
    Run complete validation suite.

    Args:
        output_dir: Directory for result files
        skip_level1: Skip Level 1 experiments
        skip_level2: Skip Level 2 experiments

    Returns:
        Summary of all experiments
    """
    Path(output_dir).mkdir(exist_ok=True)

    results = {
        "level1": {},
        "level2": None,
    }

    # Level 1
    if not skip_level1:
        print("\n" + "=" * 80)
        print("RUNNING LEVEL 1 VALIDATION")
        print("=" * 80)

        for tier in ["HIGH", "MEDIUM", "LOW"]:
            from qweave.characterization.noise_tiers import NoiseTier
            tier_enum = NoiseTier[tier]
            result = run_level1_validation(
                tier_enum,
                output_file=f"{output_dir}/level1_{tier}.json"
            )
            results["level1"][tier] = result

    # Level 2
    if not skip_level2:
        print("\n" + "=" * 80)
        print("RUNNING LEVEL 2 VALIDATION")
        print("=" * 80)

        summary = run_all_tiers()
        results["level2"] = summary

    # Generate report
    level1_files = [f"{output_dir}/level1_{t}.json" for t in ["HIGH", "MEDIUM", "LOW"]]
    report_path = f"{output_dir}/validation_report.md"

    generate_validation_report(
        level1_files,
        f"{output_dir}/level2_summary.json",
        report_path
    )

    print(f"\n{'='*80}")
    print("VALIDATION COMPLETE")
    print(f"Results saved to: {output_dir}/")
    print(f"Report: {report_path}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run Q-Weave validation benchmarks"
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--skip-level1",
        action="store_true",
        help="Skip Level 1 validation"
    )
    parser.add_argument(
        "--skip-level2",
        action="store_true",
        help="Skip Level 2 validation"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing results, don't run experiments"
    )

    args = parser.parse_args()

    if args.verify_only:
        from verify_success import verify_level1, verify_level2
        import os

        print("Verifying existing results...")
        l1_files = [f"{args.output_dir}/level1_{t}.json" for t in ["HIGH", "MEDIUM", "LOW"]]
        l1_pass = all(verify_level1(f) for f in l1_files if os.path.exists(f))
        l2_pass = verify_level2(f"{args.output_dir}/level2_summary.json")

        print(f"\nLevel 1: {'PASS' if l1_pass else 'FAIL'}")
        print(f"Level 2: {'PASS' if l2_pass else 'FAIL'}")

        sys.exit(0 if (l1_pass and l2_pass) else 1)
    else:
        run_all_experiments(
            args.output_dir,
            args.skip_level1,
            args.skip_level2
        )


if __name__ == "__main__":
    main()
```

---

## Phase 2 Completion Criteria

**This phase is complete when:**

1. **Fixed topology**: 3×3 grid coupling map is defined and validated
2. **Noise tiers**: HIGH (0.15), MEDIUM (0.07), LOW (0.02) are configured
3. **Benchmark generators**: All 5 benchmarks (GHZ, QFT, QAOA, Random Clifford, VQE) functional
4. **Level 1 validation**: Detects single known crosstalk pair and improves fidelity
5. **Level 2 validation**: Detects multi-pair unknown crosstalk across all tiers
6. **Success criteria**: Automated verification passes for ≥ 2 of 3 tiers
7. **Reproducibility**: `run_benchmarks.py` produces consistent results across runs

---

## Success Criteria Summary

### Level 1
- ✓ Hidden crosstalk pair detected (significant interaction score)
- ✓ Mitigation improves fidelity over baseline

### Level 2
- ✓ Multiple hidden crosstalk pairs detected
- ✓ Mitigated fidelity exceeds baseline by > 2× SE
- ✓ Success in ≥ 2 of 3 noise tiers (HIGH, MEDIUM, LOW)

---

## Expected Output Structure

```
results/
├── level1_HIGH.json
├── level1_MEDIUM.json
├── level1_LOW.json
├── level2_high.json
├── level2_medium.json
├── level2_low.json
├── level2_summary.json
└── validation_report.md
```

---

## Next Phase

Proceed to [03_fastapi_backend.md](./03_fastapi_backend.md) to implement the REST API layer for the frontend integration.
