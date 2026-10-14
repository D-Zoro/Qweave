"""Verify Qiskit and Aer are properly installed."""
import pytest


def test_qiskit_import():
    """Test basic Qiskit imports."""
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.converters import circuit_to_dag
    assert QuantumCircuit is not None


def test_qiskit_aer_import():
    """Test Qiskit Aer imports."""
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    assert AerSimulator is not None
    assert NoiseModel is not None


def test_dag_layer_iteration():
    """Test core DAG-based layer iteration capability."""
    from qiskit import QuantumCircuit
    from qiskit.converters import circuit_to_dag

    qc = QuantumCircuit(4)
    qc.cx(0, 1)
    qc.cx(2, 3)

    dag = circuit_to_dag(qc)
    layers = list(dag.layers())
    assert len(layers) >= 1