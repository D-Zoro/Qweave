"""Main profiler orchestrating the MEASURE phase."""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from qweave.characterization.probe_generator import ProbeGenerator, ProbeSpec
from qweave.characterization.executor import ProbeExecutor
from qweave.characterization.estimator import InteractionEstimator
from qweave.characterization.environment_injector import inject_crosstalk, create_synthetic_environment
from qweave.crosstalk_model.matrix import InteractionMatrix
from qweave.crosstalk_model.graph import CrosstalkGraph


class CrosstalkProfiler:
    """
    Main orchestrator for crosstalk characterization.

    Implements the MEASURE phase of the MEASURE → MODEL → MITIGATE → EXECUTE → EVALUATE pipeline.
    """

    def __init__(
        self,
        coupling_map: List[List[int]],
        num_qubits: int,
        simulator: Optional[AerSimulator] = None
    ):
        """
        Initialize the profiler.

        Args:
            coupling_map: List of [control, target] pairs defining hardware connectivity
            num_qubits: Number of qubits in the system
            simulator: Optional AerSimulator instance
        """
        self.coupling_map = coupling_map
        self.num_qubits = num_qubits
        self.simulator = simulator

        self.generator = ProbeGenerator(num_qubits)
        self.executor = ProbeExecutor(simulator)
        self.estimator = InteractionEstimator()

    def characterize_with_probes(
        self,
        probe_results: Dict[Tuple[int, int], Any]
    ) -> Tuple[InteractionMatrix, CrosstalkGraph]:
        """
        Build interaction matrix and graph from probe results.

        Args:
            probe_results: Mapping from gate pair to probe characterization results

        Returns:
            Tuple of (InteractionMatrix, CrosstalkGraph)
        """
        # Extract gate labels (qubit tuples) from probe results
        gate_labels = list(probe_results.keys())

        # Build interaction matrix using estimator
        matrix_array, details = self.estimator.build_interaction_matrix(
            probe_results, gate_labels
        )

        # Create InteractionMatrix
        matrix = InteractionMatrix(gate_labels, matrix_array)
        graph = CrosstalkGraph(matrix)

        return matrix, graph

    def run_full_characterization(
        self,
        noise_tier: str = "HIGH"
    ) -> Tuple[CrosstalkGraph, Dict[str, Any]]:
        """
        Run complete characterization pipeline with injected crosstalk.

        This is a convenience method for synthetic environments.

        Args:
            noise_tier: Noise tier ('HIGH', 'MEDIUM', 'LOW')

        Returns:
            Tuple of (CrosstalkGraph, metadata_dict)
        """
        # Step 1: Create synthetic environment
        hidden_rules = create_synthetic_environment(self.num_qubits, noise_tier)

        # Step 2: Generate probes for all gate pairs in coupling map
        all_probes = self.generator.generate_all_probes(self.coupling_map, max_distance=2)

        # Step 3: Execute probes with injected crosstalk
        probe_results = {}
        for gate_a, gate_b in [
            (tuple(sorted(gate)), tuple(sorted(other_gate)))
            for gate in self.coupling_map
            for other_gate in self.coupling_map
            if gate != other_gate
        ]:
            probes = self.generator.generate_probe_pair(gate_a, gate_b)
            pair_results = self.executor.characterize_pair(probes)
            probe_results[(tuple(gate_a), tuple(gate_b))] = pair_results

        # Step 4: Estimate interactions
        matrix, graph = self.characterize_with_probes(probe_results)

        metadata = {
            "noise_tier": noise_tier,
            "num_qubits": self.num_qubits,
            "num_gates": len(self.coupling_map),
            "num_probe_pairs": len(probe_results),
            "hidden_rules_count": len(hidden_rules)
        }

        return graph, metadata


class SyntheticCrosstalkProfiler:
    """
    Profiler for synthetic crosstalk experiments.

    Injects known crosstalk so we can validate the profiling pipeline.
    """

    def __init__(
        self,
        coupling_map: List[List[int]],
        num_qubits: int,
        simulator: Optional[AerSimulator] = None
    ):
        self.profiler = CrosstalkProfiler(coupling_map, num_qubits, simulator)
        self.simulator = simulator or AerSimulator()

    def experiment_with_tier(
        self,
        tier: str = "HIGH"
    ) -> Tuple[CrosstalkGraph, Dict[str, Any]]:
        """Run a full synthetic experiment for a given noise tier."""
        return self.profiler.run_full_characterization(tier)

    def compare_tiers(
        self,
        tiers: List[str] = ["HIGH", "MEDIUM", "LOW"]
    ) -> Dict[str, Tuple[CrosstalkGraph, Dict[str, Any]]]:
        """
        Run characterization across multiple noise tiers.

        Returns:
            Mapping from tier to (graph, metadata) tuples
        """
        results = {}
        for tier in tiers:
            graph, metadata = self.experiment_with_tier(tier)
            results[tier] = (graph, metadata)

        return results

    def validate_characterization(
        self,
        true_interactions: Dict[frozenset, float],
        estimated_graph: CrosstalkGraph
    ) -> Dict[str, float]:
        """
        Validate characterization against known ground truth.

        Args:
            true_interactions: Ground truth interaction rules
            estimated_graph: Graph from profiling

        Returns:
            Validation metrics (true positive rate, false positive rate, etc.)
        """
        # Convert estimated graph to interaction set
        estimated_interactions = set()
        for node_a, node_b, data in estimated_graph.graph.edges(data=True):
            # Get the gate labels
            label_a = estimated_graph.graph.nodes[node_a].get("label", tuple())
            label_b = estimated_graph.graph.nodes[node_b].get("label", tuple())

            # Check which pairs interact
            for pair1, pair2 in true_interactions.keys():
                if frozenset([tuple(label_a), tuple(label_b)]) == frozenset([pair1, pair2]):
                    estimated_interactions.add(frozenset([pair1, pair2]))

        true_interaction_set = set(true_interactions.keys())

        # Calculate metrics
        true_positives = len(true_interaction_set & estimated_interactions)
        false_positives = len(estimated_interactions - true_interaction_set)
        false_negatives = len(true_interaction_set - estimated_interactions)
        true_negatives = len(get_all_possible_pairs()) - true_positives - false_positives - false_negatives

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_negatives": true_negatives,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }

    def get_all_possible_pairs(self) -> set:
        """Get all possible gate pairs in the coupling map."""
        import itertools
        base_gates = [tuple(sorted(pair)) for pair in self.profiler.coupling_map]
        return set(itertools.combinations(base_gates, 2))