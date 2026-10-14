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