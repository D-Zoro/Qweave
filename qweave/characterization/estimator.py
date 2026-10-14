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