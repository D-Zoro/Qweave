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