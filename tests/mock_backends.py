"""Mock backends for testing without Aer simulator overhead."""

from unittest.mock import MagicMock
from qiskit_aer.noise import NoiseModel


class MockNoiseSimulator:
    """Mock simulator for fast unit tests."""

    def __init__(self, noise_model=None):
        self.noise_model = noise_model or NoiseModel()
        self.run_count = 0

    def run(self, circuit, shots=8192, seed=None):
        """Mock run that returns predetermined results."""
        self.run_count += 1
        mock_result = MagicMock()
        # Simulate perfect execution for testing
        mock_result.get_counts.return_value = {"0" * circuit.num_clbits: shots}
        mock_result.success = True
        return mock_result

    def set_options(self, **kwargs):
        pass


def create_mock_3x3_backend():
    """Create a mock backend with 3x3 grid topology."""
    backend = MagicMock()
    backend.num_qubits = 9
    backend.configuration.return_value = MagicMock(
        coupling_map=[
            [0, 1], [1, 0], [1, 2], [2, 1],
            [0, 3], [3, 0], [1, 4], [4, 1], [2, 5], [5, 2],
            [3, 4], [4, 3], [4, 5], [5, 4],
            [3, 6], [6, 3], [4, 7], [7, 4], [5, 8], [8, 5],
            [6, 7], [7, 6], [7, 8], [8, 7],
        ]
    )
    return backend