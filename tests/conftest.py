"""Pytest fixtures and configuration for Q-Weave tests."""

import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel


@pytest.fixture
def simulator():
    """Return a Qiskit Aer simulator instance."""
    return AerSimulator()


@pytest.fixture
def simple_circuit():
    """Return a simple test circuit."""
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(2, 3)
    qc.measure_all()
    return qc


@pytest.fixture
def noiseless_noise_model():
    """Return an empty noise model."""
    return NoiseModel()


@pytest.fixture
def grid_coupling_map():
    """Return a 3x3 grid coupling map (9 qubits)."""
    return [
        [0, 1], [1, 0],
        [1, 2], [2, 1],
        [0, 3], [3, 0],
        [1, 4], [4, 1],
        [2, 5], [5, 2],
        [3, 4], [4, 3],
        [4, 5], [5, 4],
        [3, 6], [6, 3],
        [4, 7], [7, 4],
        [5, 8], [8, 5],
        [6, 7], [7, 6],
        [7, 8], [8, 7],
    ]