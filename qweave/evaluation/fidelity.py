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