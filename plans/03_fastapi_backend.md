# Phase 3: FastAPI Backend

## Objective
Implement an asynchronous FastAPI server that exposes the Q-Weave compiler pipeline through RESTful endpoints. The backend serves as the bridge between the core compiler engine and the Next.js frontend dashboard.

---

## Architecture Overview

```
qweave_api/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── models.py               # Pydantic data models
├── deps.py                 # Dependency injection
├── routers/
│   ├── __init__.py
│   ├── characterization.py # /api/characterize endpoints
│   ├── graph.py            # /api/graph endpoints
│   ├── mitigation.py       # /api/mitigate endpoints
│   └── evaluation.py       # /api/evaluate endpoints
├── core/
│   ├── __init__.py
│   ├── config.py           # Application configuration
│   ├── state.py            # Shared state management
│   └── cache.py            # Simple in-memory cache
└── utils/
    ├── __init__.py
    ├── circuit_parser.py   # Circuit JSON serialization
    └── response.py         # Response helpers
```

---

## Step 1: Pydantic Data Models

**File:** `qweave_api/models.py`

### Purpose
Define all data models for request/response serialization using Pydantic v2.

### Implementation

```python
"""Pydantic data models for Q-Weave API."""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum

# ============================================================================
# Enums
# ============================================================================

class NoiseTier(str, Enum):
    """Noise severity tiers for synthetic crosstalk."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BenchmarkType(str, Enum):
    """Available benchmark circuit types."""
    GHZ = "GHZ"
    QFT = "QFT"
    QAOA = "QAOA"
    RANDOM_CLIFFORD = "RANDOM_CLIFFORD"
    VQE = "VQE"


# ============================================================================
# Request Models
# ============================================================================

class CircuitInput(BaseModel):
    """Input quantum circuit in Qiskit QASM or JSON format."""
    qasm: Optional[str] = Field(
        None,
        description="QASM string representation of the circuit"
    )
    json_circuit: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON-serialized circuit (Qiskit qpy or custom format)"
    )
    num_qubits: int = Field(
        ...,
        ge=2,
        le=127,
        description="Number of qubits in the circuit"
    )
    name: Optional[str] = Field(
        None,
        description="Optional circuit name"
    )


class CharacterizeRequest(BaseModel):
    """Request for crosstalk characterization."""
    circuit: CircuitInput
    noise_tier: NoiseTier = Field(
        NoiseTier.MEDIUM,
        description="Synthetic noise tier level"
    )
    coupling_map: Optional[List[List[int]]] = Field(
        None,
        description="Custom coupling map (defaults to 3x3 grid)"
    )
    max_distance: int = Field(
        2,
        ge=1,
        le=10,
        description="Maximum hops between operations to probe"
    )
    shots: int = Field(
        8192,
        ge=1024,
        le=65536,
        description="Number of shots per probe circuit"
    )
    use_cached: bool = Field(
        False,
        description="Use cached results if available"
    )


class MitigateRequest(BaseModel):
    """Request for crosstalk-aware mitigation."""
    circuit: CircuitInput
    characterization_id: Optional[str] = Field(
        None,
        description="ID of previous characterization (optional, will re-run if omitted)"
    )
    noise_tier: NoiseTier = Field(
        NoiseTier.MEDIUM,
        description="Synthetic noise tier for evaluation"
    )
    apply_placement: bool = Field(
        True,
        description="Apply crosstalk-aware qubit placement"
    )
    apply_scheduling: bool = Field(
        True,
        description="Apply crosstalk-aware scheduling"
    )


class EvaluationRequest(BaseModel):
    """Request for baseline vs Q-Weave evaluation."""
    circuit: CircuitInput
    noise_tier: NoiseTier = Field(
        NoiseTier.MEDIUM,
        description="Synthetic noise tier for evaluation"
    )
    characterization_id: Optional[str] = Field(
        None,
        description="Cached characterization ID"
    )
    mitigation_id: Optional[str] = Field(
        None,
        description="Cached mitigation ID"
    )
    shots: int = Field(
        8192,
        ge=1024,
        le=65536,
        description="Number of execution shots"
    )
    runs: int = Field(
        1,
        ge=1,
        le=10,
        description="Number of independent evaluation runs"
    )


class BenchmarkRequest(BaseModel):
    """Request to run a predefined benchmark."""
    benchmark_type: BenchmarkType
    num_qubits: int = Field(
        4,
        ge=2,
        le=9,
        description="Number of qubits for the benchmark"
    )
    noise_tier: NoiseTier = NoiseTier.MEDIUM


# ============================================================================
# Response Models
# ============================================================================

class JobStatus(BaseModel):
    """Status of an async job."""
    job_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    progress: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Progress percentage (0.0 to 1.0)"
    )
    message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class ProbeResult(BaseModel):
    """Result of a single probe execution."""
    probe_name: str
    probe_type: str
    targets: List[List[int]]
    fidelity: float
    standard_error: float
    shots: int
    seed: int


class InteractionEstimate(BaseModel):
    """Interaction estimate between two operations."""
    operation_a: str
    operation_b: str
    expectation: float
    raw_degradation: float
    combined_se: float
    significance: float
    interaction_score: float
    is_significant: bool


class InteractionMatrixResponse(BaseModel):
    """Response containing interaction matrix data."""
    characterization_id: str
    labels: List[List[int]]
    matrix: List[List[float]]
    num_operations: int
    noise_tier: str


class GraphNode(BaseModel):
    """Node in the crosstalk interaction graph."""
    id: int
    label: str
    qubits: List[int]


class GraphEdge(BaseModel):
    """Edge in the crosstalk interaction graph."""
    source: int
    target: int
    weight: float


class CrosstalkGraphResponse(BaseModel):
    """Response containing crosstalk graph data."""
    characterization_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    max_interaction: float


class ScheduleLayer(BaseModel):
    """Single layer in a schedule."""
    layer_index: int
    operations: List[Dict[str, Any]]
    num_operations: int


class ScheduleResponse(BaseModel):
    """Response containing schedule information."""
    original_depth: int
    scheduled_depth: int
    layers: List[ScheduleLayer]
    total_crosstalk_exposure: float


class MitigationMetrics(BaseModel):
    """Metrics from mitigation process."""
    original_depth: int
    mitigated_depth: int
    original_two_qubit_gates: int
    mitigated_two_qubit_gates: int
    depth_change: int
    depth_change_percent: float
    schedule_layers: int
    qubit_mapping: Dict[str, int]


class MitigationResponse(BaseModel):
    """Response from mitigation endpoint."""
    mitigation_id: str
    characterization_id: str
    circuit_qasm: str
    metrics: MitigationMetrics


class ExecutionCounts(BaseModel):
    """Measurement counts from circuit execution."""
    counts: Dict[str, int]
    shots: int


class FidelityMetrics(BaseModel):
    """Fidelity comparison metrics."""
    baseline_fidelity: float
    mitigated_fidelity: float
    improvement: float
    improvement_percent: float


class EvaluationResponse(BaseModel):
    """Response from evaluation endpoint."""
    evaluation_id: str
    baseline: ExecutionCounts
    mitigated: ExecutionCounts
    fidelity: FidelityMetrics
    metrics: MitigationMetrics
    noise_tier: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "0.1.0"
    qiskit_version: str
    aer_version: str
```

---

## Step 2: Application Configuration

**File:** `qweave_api/core/config.py`

```python
"""Application configuration."""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Q-Weave API"
    APP_DESCRIPTION: str = "Crosstalk-aware quantum circuit mitigation API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1  # Single worker for stateful operations

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # Paths
    RESULTS_DIR: str = "./results"
    CACHE_DIR: str = "./cache"

    # Execution defaults
    DEFAULT_SHOTS: int = 8192
    MAX_SHOTS: int = 65536
    DEFAULT_NOISE_TIER: str = "MEDIUM"

    # Performance
    REQUEST_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_JOBS: int = 4

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def ensure_directories():
    """Create necessary directories if they don't exist."""
    settings = get_settings()
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    os.makedirs(settings.CACHE_DIR, exist_ok=True)
```

---

## Step 3: State Management

**File:** `qweave_api/core/state.py`

```python
"""In-memory state management for characterization and mitigation results."""

import uuid
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class CharacterizationState:
    """Stored state of a characterization run."""
    id: str
    noise_tier: str
    coupling_map: list
    interaction_matrix: Any  # numpy array
    interaction_graph: Any  # NetworkX graph
    estimates: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "completed"


@dataclass
class MitigationState:
    """Stored state of a mitigation run."""
    id: str
    characterization_id: str
    circuit_qasm: str
    metrics: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "completed"


class StateManager:
    """Thread-safe state manager for job results."""

    def __init__(self):
        self._characterizations: Dict[str, CharacterizationState] = {}
        self._mitigations: Dict[str, MitigationState] = {}
        self._lock = threading.RLock()

    def create_characterization_id(self) -> str:
        """Generate new characterization ID."""
        return f"char_{uuid.uuid4().hex[:12]}"

    def create_mitigation_id(self) -> str:
        """Generate new mitigation ID."""
        return f"mit_{uuid.uuid4().hex[:12]}"

    def store_characterization(
        self,
        state: CharacterizationState
    ) -> str:
        """Store characterization result."""
        with self._lock:
            self._characterizations[state.id] = state
        return state.id

    def store_mitigation(self, state: MitigationState) -> str:
        """Store mitigation result."""
        with self._lock:
            self._mitigations[state.id] = state
        return state.id

    def get_characterization(self, char_id: str) -> Optional[CharacterizationState]:
        """Retrieve characterization by ID."""
        with self._lock:
            return self._characterizations.get(char_id)

    def get_mitigation(self, mit_id: str) -> Optional[MitigationState]:
        """Retrieve mitigation by ID."""
        with self._lock:
            return self._mitigations.get(mit_id)

    def list_characterizations(self) -> Dict[str, str]:
        """List all characterization IDs with timestamps."""
        with self._lock:
            return {
                k: v.timestamp for k, v in self._characterizations.items()
            }

    def clear_old(self, max_age_hours: int = 24):
        """Clear results older than specified hours."""
        # Implementation for cache cleanup
        pass


# Global state manager instance
state_manager = StateManager()
```

---

## Step 4: Main Application

**File:** `qweave_api/main.py`

```python
"""FastAPI application entry point."""

import qiskit
from qiskit_aer import Aer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from qweave_api.core.config import get_settings, ensure_directories
from qweave_api.core.state import state_manager
from qweave_api.models import HealthResponse, ErrorResponse

# Import routers
from qweave_api.routers import (
    characterization,
    graph,
    mitigation,
    evaluation,
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        characterization.router,
        prefix="/api",
        tags=["characterization"]
    )
    app.include_router(
        graph.router,
        prefix="/api",
        tags=["graph"]
    )
    app.include_router(
        mitigation.router,
        prefix="/api",
        tags=["mitigation"]
    )
    app.include_router(
        evaluation.router,
        prefix="/api",
        tags=["evaluation"]
    )

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error=str(exc)).dict()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc) if settings.DEBUG else None
            ).dict()
        )

    # Startup/shutdown events
    @app.on_event("startup")
    async def startup_event():
        ensure_directories()
        print(f"Q-Weave API v{settings.APP_VERSION} starting up...")

    @app.on_event("shutdown")
    async def shutdown_event():
        print("Shutting down Q-Weave API...")

    return app


app = create_app()


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health check."""
    return HealthResponse(
        status="ok",
        version=get_settings().APP_VERSION,
        qiskit_version=qiskit.__version__,
        aer_version=Aer.__version__ if hasattr(Aer, '__version__') else "unknown"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version=get_settings().APP_VERSION,
        qiskit_version=qiskit.__version__,
        aer_version=Aer.__version__ if hasattr(Aer, '__version__') else "unknown"
    )


@app.get("/api/state")
async def get_state_summary():
    """Get summary of stored state (for debugging)."""
    return {
        "characterizations": state_manager.list_characterizations(),
        "mitigations_count": len(state_manager._mitigations),
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "qweave_api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS
    )
```

---

## Step 5: Characterization Router

**File:** `qweave_api/routers/characterization.py`

```python
"""Characterization API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from qweave_api.models import (
    CharacterizeRequest,
    CharacterizeResponse,
    InteractionMatrixResponse,
    ProbeResult,
    InteractionEstimate,
    JobStatus,
    NoiseTier,
    BenchmarkType,
    BenchmarkRequest,
)
from qweave_api.core.state import state_manager, CharacterizationState
from qweave_api.core.config import get_settings

from qweave.hardware.topology import get_grid_3x3_topology
from qweave.characterization.noise_tiers import (
    NOISE_TIER_CONFIGS,
    NoiseTier as CoreNoiseTier
)
from qweave.characterization.environment_injector import inject_crosstalk
from qweave.characterization.probe_generator import ProbeGenerator
from qweave.characterization.executor import ProbeExecutor
from qweave.characterization.estimator import InteractionEstimator
from qweave.crosstalk_model.matrix import InteractionMatrix
from qweave.crosstalk_model.graph import CrosstalkGraph
from qweave.evaluation.benchmarks import BenchmarkGenerator

import numpy as np
import uuid
from datetime import datetime


router = APIRouter()


# In-memory job tracking (replace with proper job queue for production)
_jobs: dict = {}


def _noise_tier_to_core(tier: NoiseTier) -> CoreNoiseTier:
    """Convert API noise tier to core enum."""
    mapping = {
        NoiseTier.HIGH: CoreNoiseTier.HIGH,
        NoiseTier.MEDIUM: CoreNoiseTier.MEDIUM,
        NoiseTier.LOW: CoreNoiseTier.LOW,
    }
    return mapping[tier]


def _run_characterization_sync(
    job_id: str,
    request: CharacterizeRequest
) -> str:
    """Synchronous characterization runner."""
    try:
        _jobs[job_id]["status"] = "running"
        _jobs[job_id]["progress"] = 0.1

        # Get topology
        if request.coupling_map:
            coupling_map = request.coupling_map
            num_qubits = max(max(p) for p in coupling_map) + 1
        else:
            topology = get_grid_3x3_topology()
            coupling_map = topology.coupling_map
            num_qubits = topology.num_qubits

        _jobs[job_id]["progress"] = 0.2

        # Generate probes
        probe_gen = ProbeGenerator(num_qubits)
        all_probes = probe_gen.generate_all_probes(coupling_map, request.max_distance)

        _jobs[job_id]["progress"] = 0.3

        # Create synthetic environment if circuit provided
        noise_model = None
        if request.circuit.name:
            hidden_rules = create_synthetic_environment(num_qubits, request.noise_tier.value)
            dummy_qc = QuantumCircuit(num_qubits)
            _, noise_model = inject_crosstalk(dummy_qc, hidden_rules)

        _jobs[job_id]["progress"] = 0.4

        # Execute probes
        simulator = AerSimulator()
        executor = ProbeExecutor(simulator)

        pair_results = {}
        total_probes = len(all_probes)

        for i in range(0, total_probes, 3):
            if i + 2 < total_probes:
                probes = [all_probes[i], all_probes[i+1], all_probes[i+2]]
                results = {}
                for probe in probes:
                    result = executor.execute_with_repeats(
                        probe, noise_model, request.shots
                    )
                    results[probe.type] = result

                pair_key = (str(probes[0].targets[0]), str(probes[1].targets[0]))
                pair_results[pair_key] = results

                progress = 0.4 + (0.5 * (i / total_probes))
                _jobs[job_id]["progress"] = progress

        _jobs[job_id]["progress"] = 0.9

        # Estimate interactions
        estimator = InteractionEstimator()
        estimates = {}
        labels = []
        matrix_data = []

        for pair_key, probe_data in pair_results.items():
            estimate = estimator.estimate_from_probe_results(probe_data)

            if estimate['is_significant']:
                labels.append(eval(pair_key[0]))  # Convert string back to tuple
                estimates[pair_key] = estimate

        # Build matrix
        n = len(labels)
        if n > 0:
            matrix = np.zeros((n, n))
            for i in range(n):
                for j in range(n):
                    pair = (str(labels[i]), str(labels[j]))
                    if pair in estimates:
                        matrix[i, j] = estimates[pair]['interaction_score']
        else:
            matrix = np.zeros((1, 1))
            labels = [(0, 1)]

        _jobs[job_id]["progress"] = 1.0

        # Store result
        char_id = state_manager.create_characterization_id()
        state = CharacterizationState(
            id=char_id,
            noise_tier=request.noise_tier.value,
            coupling_map=coupling_map,
            interaction_matrix=matrix,
            interaction_graph=CrosstalkGraph.from_matrix(
                InteractionMatrix(labels, matrix)
            ),
            estimates=estimates
        )
        state_manager.store_characterization(state)

        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result_id"] = char_id

        return char_id

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        raise


@router.post("/characterize", response_model=JobStatus)
async def characterize(
    request: CharacterizeRequest,
    background_tasks: BackgroundTasks
):
    """
    Run crosstalk characterization on a quantum circuit.

    This endpoint initiates a characterization job that:
    1. Generates probe circuits for candidate gate pairs
    2. Executes them with synthetic crosstalk
    3. Estimates interaction strengths
    4. Returns an interaction matrix

    Returns a job ID for polling status.
    """
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    _jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.now().isoformat(),
    }

    # Run in background
    background_tasks.add_task(_run_characterization_sync, job_id, request)

    return JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Characterization job queued",
        created_at=_jobs[job_id]["created_at"]
    )


@router.get("/characterize/{job_id}/status", response_model=JobStatus)
async def get_characterization_status(job_id: str):
    """Get status of a characterization job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job.get("status", "unknown"),
        progress=job.get("progress"),
        message=job.get("message"),
        created_at=job.get("created_at"),
        completed_at=job.get("completed_at") if job.get("status") == "completed" else None
    )


@router.get("/characterize/{job_id}/result", response_model=InteractionMatrixResponse)
async def get_characterization_result(job_id: str):
    """Get the result of a completed characterization job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _jobs[job_id]
    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job.get('status')}"
        )

    char_id = job.get("result_id")
    state = state_manager.get_characterization(char_id)

    if not state:
        raise HTTPException(status_code=404, detail="Characterization result not found")

    matrix = state.interaction_matrix

    return InteractionMatrixResponse(
        characterization_id=char_id,
        labels=[list(label) for label in state.estimates.keys()],
        matrix=matrix.tolist() if hasattr(matrix, 'tolist') else [[0.0]],
        num_operations=len(state.estimates),
        noise_tier=state.noise_tier
    )


@router.post("/benchmark")
async def run_benchmark(request: BenchmarkRequest):
    """Generate a benchmark circuit."""
    gen = BenchmarkGenerator()

    circuits = {
        BenchmarkType.GHZ: gen.ghz_circuit,
        BenchmarkType.QFT: gen.qft_circuit,
        BenchmarkType.QAOA: gen.qaoa_circuit,
        BenchmarkType.RANDOM_CLIFFORD: gen.random_clifford,
        BenchmarkType.VQE: gen.vqe_circuit,
    }

    if request.benchmark_type not in circuits:
        raise HTTPException(status_code=400, detail="Unknown benchmark type")

    circuit = circuits[request.benchmark_type](request.num_qubits)

    return {
        "name": circuit.name,
        "num_qubits": circuit.num_qubits,
        "depth": circuit.depth(),
        "num_nonlocal_gates": circuit.num_nonlocal_gates(),
        "qasm": circuit.qasm(),
    }


def create_synthetic_environment(num_qubits: int, tier: str) -> dict:
    """Create synthetic environment with random crosstalk rules."""
    import random
    prob = NOISE_TIER_CONFIGS[_noise_tier_to_core(NoiseTier(tier))].depolarizing_probability

    rules = {}
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

## Step 6: Graph Router

**File:** `qweave_api/routers/graph.py`

```python
"""Graph visualization API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from qweave_api.models import (
    CrosstalkGraphResponse,
    GraphNode,
    GraphEdge,
)
from qweave_api.core.state import state_manager


router = APIRouter()


@router.get("/graph/{characterization_id}", response_model=CrosstalkGraphResponse)
async def get_graph(characterization_id: str):
    """
    Get the crosstalk interaction graph for visualization.

    Returns nodes (operations) and edges (interactions) with weights
    suitable for rendering in a network graph visualization.
    """
    state = state_manager.get_characterization(characterization_id)

    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Characterization {characterization_id} not found"
        )

    graph = state.interaction_graph
    nx_graph = graph.to_networkx()

    # Build nodes
    nodes = []
    for node_id, data in nx_graph.nodes(data=True):
        nodes.append(GraphNode(
            id=node_id,
            label=str(data.get("label", f"Gate {node_id}")),
            qubits=list(data.get("qubits", []))
        ))

    # Build edges
    edges = []
    max_weight = 0.0
    for u, v, data in nx_graph.edges(data=True):
        weight = data.get("weight", 0.0)
        max_weight = max(max_weight, weight)
        edges.append(GraphEdge(
            source=u,
            target=v,
            weight=weight
        ))

    return CrosstalkGraphResponse(
        characterization_id=characterization_id,
        nodes=nodes,
        edges=edges,
        max_interaction=max_weight if max_weight > 0 else 1.0
    )


@router.get("/graph/{characterization_id}/matrix")
async def get_matrix_data(characterization_id: str):
    """
    Get the interaction matrix as structured data.

    Returns the full matrix with labels for heatmap visualization.
    """
    state = state_manager.get_characterization(characterization_id)

    if not state:
        raise HTTPException(status_code=404, detail="Characterization not found")

    matrix = state.interaction_matrix

    # Get labels from estimates
    labels = [str(k) for k in state.estimates.keys()]

    return {
        "labels": labels,
        "matrix": matrix.tolist() if hasattr(matrix, 'tolist') else matrix,
        "shape": matrix.shape if hasattr(matrix, 'shape') else (0, 0),
    }


@router.get("/graph/{characterization_id}/strongest")
async def get_strongest_interactions(
    characterization_id: str,
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.0, ge=0.0, le=1.0)
):
    """
    Get the strongest crosstalk interactions.

    Useful for highlighting critical edges in the visualization.
    """
    state = state_manager.get_characterization(characterization_id)

    if not state:
        raise HTTPException(status_code=404, detail="Characterization not found")

    graph = state.interaction_graph
    nx_graph = graph.to_networkx()

    # Get all edges sorted by weight
    edges = []
    for u, v, data in nx_graph.edges(data=True):
        weight = data.get("weight", 0.0)
        if weight >= threshold:
            edges.append({
                "source": u,
                "target": v,
                "weight": weight,
            })

    edges.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "interactions": edges[:limit],
        "total_count": len(edges),
    }
```

---

## Step 7: Mitigation Router

**File:** `qweave_api/routers/mitigation.py`

```python
"""Mitigation API endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from qweave_api.models import (
    MitigateRequest,
    MitigationResponse,
    MitigationMetrics,
    ScheduleLayer,
    JobStatus,
)
from qweave_api.core.state import state_manager, MitigationState
from qweave_api.core.config import get_settings

from qweave.hardware.topology import get_grid_3x3_topology
from qweave.characterization.noise_tiers import (
    NOISE_TIER_CONFIGS,
    NoiseTier as CoreNoiseTier
)
from qweave.characterization.environment_injector import inject_crosstalk, create_synthetic_environment
from qweave.characterization.probe_generator import ProbeGenerator
from qweave.characterization.executor import ProbeExecutor
from qweave.characterization.estimator import InteractionEstimator
from qweave.crosstalk_model.matrix import InteractionMatrix
from qweave.crosstalk_model.graph import CrosstalkGraph
from qweave.mitigation.engine import MitigationEngine

import uuid
from datetime import datetime


router = APIRouter()
_mitigation_jobs: dict = {}


def _noise_tier_to_core(tier: str) -> CoreNoiseTier:
    """Convert string tier to core enum."""
    return CoreNoiseTier[tier.upper()]


def _run_mitigation_sync(
    job_id: str,
    request: MitigateRequest
) -> str:
    """Synchronous mitigation runner."""
    try:
        _mitigation_jobs[job_id]["status"] = "running"
        _mitigation_jobs[job_id]["progress"] = 0.1

        # Build circuit from input
        if request.circuit.qasm:
            circuit = QuantumCircuit.from_qasm_str(request.circuit.qasm)
        else:
            # Create simple circuit from defaults
            n = request.circuit.num_qubits
            circuit = QuantumCircuit(n)
            circuit.h(0)
            for i in range(n - 1):
                circuit.cx(i, i + 1)

        _mitigation_jobs[job_id]["progress"] = 0.2

        # Get or create characterization
        if request.characterization_id:
            char_state = state_manager.get_characterization(request.characterization_id)
            if not char_state:
                raise ValueError(f"Characterization {request.characterization_id} not found")
        else:
            # Run characterization
            topology = get_grid_3x3_topology()
            num_qubits = topology.num_qubits

            hidden_rules = create_synthetic_environment(
                num_qubits,
                request.noise_tier.value
            )

            dummy_qc = QuantumCircuit(num_qubits)
            _, noise_model = inject_crosstalk(dummy_qc, hidden_rules)

            probe_gen = ProbeGenerator(num_qubits)
            all_probes = probe_gen.generate_all_probes(topology.coupling_map)

            simulator = AerSimulator()
            executor = ProbeExecutor(simulator)

            pair_results = {}
            for i in range(0, len(all_probes), 3):
                if i + 2 < len(all_probes):
                    probes = [all_probes[i], all_probes[i+1], all_probes[i+2]]
                    results = {}
                    for probe in probes:
                        result = executor.execute_with_repeats(
                            probe, noise_model, 8192
                        )
                        results[probe.type] = result

                    pair_key = (str(probes[0].targets[0]), str(probes[1].targets[0]))
                    pair_results[pair_key] = results

            estimator = InteractionEstimator()
            estimates = {}
            labels = []

            import numpy as np
            for pair_key, probe_data in pair_results.items():
                est = estimator.estimate_from_probe_results(probe_data)
                if est['is_significant']:
                    labels.append(eval(pair_key[0]))
                    estimates[pair_key] = est

            n_ops = len(labels) if labels else 1
            matrix = np.zeros((n_ops, n_ops))
            for state_char_id in estimates:
                # Simplified matrix construction
                pass

            if not labels:
                labels = [(0, 1)]
                matrix = np.array([[0.0]])

            inter_matrix = InteractionMatrix(labels, matrix)
            char_id = state_manager.create_characterization_id()
            char_state = CharacterizationState(
                id=char_id,
                noise_tier=request.noise_tier.value,
                coupling_map=topology.coupling_map,
                interaction_matrix=matrix,
                interaction_graph=CrosstalkGraph.from_matrix(inter_matrix),
                estimates=estimates
            )
            state_manager.store_characterization(char_state)

        _mitigation_jobs[job_id]["progress"] = 0.6

        # Run mitigation
        graph = char_state.interaction_graph

        # Get coupling map from state or default
        coupling_map = char_state.coupling_map if char_state.coupling_map else get_grid_3x3_topology().coupling_map

        engine = MitigationEngine(graph, coupling_map)
        result = engine.mitigate(circuit)

        _mitigation_jobs[job_id]["progress"] = 0.9

        # Store result
        mit_id = state_manager.create_mitigation_id()
        metrics = result.metrics

        mit_state = MitigationState(
            id=mit_id,
            characterization_id=char_state.id,
            circuit_qasm=result.mitigated_circuit.qasm(),
            metrics={
                "original_depth": metrics["original_depth"],
                "mitigated_depth": metrics["mitigated_depth"],
                "original_two_qubit_gates": metrics["original_two_qubit_gates"],
                "mitigated_two_qubit_gates": metrics["mitigated_two_qubit_gates"],
                "depth_change": metrics["depth_change"],
                "depth_change_percent": metrics["depth_change_percent"],
                "schedule_layers": metrics["schedule_layers"],
                "qubit_mapping": {str(k): v for k, v in metrics["qubit_mapping"].items()},
            }
        )
        state_manager.store_mitigation(mit_state)

        _mitigation_jobs[job_id]["progress"] = 1.0
        _mitigation_jobs[job_id]["status"] = "completed"
        _mitigation_jobs[job_id]["result_id"] = mit_id

        return mit_id

    except Exception as e:
        _mitigation_jobs[job_id]["status"] = "failed"
        _mitigation_jobs[job_id]["error"] = str(e)
        raise


@router.post("/mitigate", response_model=JobStatus)
async def mitigate(
    request: MitigateRequest,
    background_tasks: BackgroundTasks
):
    """
    Apply crosstalk-aware mitigation to a quantum circuit.

    This endpoint runs both placement optimization and scheduling
    if requested, using a previously computed or fresh characterization.

    Returns a job ID for polling status.
    """
    job_id = f"mit_job_{uuid.uuid4().hex[:12]}"
    _mitigation_jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.now().isoformat(),
    }

    background_tasks.add_task(_run_mitigation_sync, job_id, request)

    return JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Mitigation job queued",
        created_at=_mitigation_jobs[job_id]["created_at"]
    )


@router.get("/mitigate/{job_id}/status", response_model=JobStatus)
async def get_mitigation_status(job_id: str):
    """Get status of a mitigation job."""
    if job_id not in _mitigation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _mitigation_jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job.get("status", "unknown"),
        progress=job.get("progress"),
        message=job.get("message"),
        created_at=job.get("created_at"),
        completed_at=job.get("completed_at") if job.get("status") == "completed" else None
    )


@router.get("/mitigate/{job_id}/result", response_model=MitigationResponse)
async def get_mitigation_result(job_id: str):
    """Get the result of a completed mitigation job."""
    if job_id not in _mitigation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _mitigation_jobs[job_id]
    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job.get('status')}"
        )

    mit_id = job.get("result_id")
    state = state_manager.get_mitigation(mit_id)

    if not state:
        raise HTTPException(status_code=404, detail="Mitigation result not found")

    metrics = state.metrics

    return MitigationResponse(
        mitigation_id=mit_id,
        characterization_id=state.characterization_id,
        circuit_qasm=state.circuit_qasm,
        metrics=MitigationMetrics(
            original_depth=metrics["original_depth"],
            mitigated_depth=metrics["mitigated_depth"],
            original_two_qubit_gates=metrics["original_two_qubit_gates"],
            mitigated_two_qubit_gates=metrics["mitigated_two_qubit_gates"],
            depth_change=metrics["depth_change"],
            depth_change_percent=metrics["depth_change_percent"],
            schedule_layers=metrics["schedule_layers"],
            qubit_mapping=metrics["qubit_mapping"],
        )
    )


@router.get("/mitigate/{mitigation_id}/schedule")
async def get_schedule(mitigation_id: str):
    """Get the detailed schedule from mitigation."""
    state = state_manager.get_mitigation(mitigation_id)

    if not state:
        raise HTTPException(status_code=404, detail="Mitigation not found")

    # Schedule is stored in metrics
    return {
        "mitigation_id": mitigation_id,
        "layers": state.metrics.get("schedule_layers", 0),
        "qubit_mapping": state.metrics.get("qubit_mapping", {}),
    }
```

---

## Step 8: Evaluation Router

**File:** `qweave_api/routers/evaluation.py`

```python
"""Evaluation API endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from qweave_api.models import (
    EvaluationRequest,
    EvaluationResponse,
    ExecutionCounts,
    FidelityMetrics,
    MitigationMetrics,
    JobStatus,
)
from qweave_api.core.state import state_manager
from qweave_api.core.config import get_settings

from qweave.evaluation.fidelity import hellinger_fidelity
from qweave.evaluation.benchmarks import BenchmarkGenerator

import uuid
import numpy as np
from datetime import datetime
from typing import List, Dict, Any


router = APIRouter()
_eval_jobs: dict = {}


def _run_evaluation_sync(
    job_id: str,
    request: EvaluationRequest
) -> dict:
    """Synchronous evaluation runner."""
    try:
        _eval_jobs[job_id]["status"] = "running"
        _eval_jobs[job_id]["progress"] = 0.1

        # Build or retrieve mitigated circuit
        if request.mitigation_id:
            mit_state = state_manager.get_mitigation(request.mitigation_id)
            if not mit_state:
                raise ValueError(f"Mitigation {request.mitigation_id} not found")
            mitigated_circuit = QuantumCircuit.from_qasm_str(mit_state.circuit_qasm)
            char_id = mit_state.characterization_id
            mit_metrics = mit_state.metrics
        else:
            # Would need to run mitigation - simplified for API
            raise ValueError("Mitigation ID required for evaluation")

        # Build original circuit
        if request.circuit.qasm:
            original_circuit = QuantumCircuit.from_qasm_str(request.circuit.qasm)
        else:
            n = request.circuit.num_qubits
            original_circuit = QuantumCircuit(n)
            original_circuit.h(0)
            for i in range(n - 1):
                original_circuit.cx(i, i + 1)
            original_circuit.measure_all()

        _eval_jobs[job_id]["progress"] = 0.3

        # Get coupling map from characterization
        char_state = state_manager.get_characterization(char_id)
        coupling_map = char_state.coupling_map if char_state else None

        # Create baseline (Qiskit transpilation)
        simulator = AerSimulator()
        baseline = transpile(
            original_circuit,
            simulator,
            coupling_map=coupling_map,
            optimization_level=3
        )

        _eval_jobs[job_id]["progress"] = 0.5

        # Execute baseline
        shots = request.shots
        baseline_job = simulator.run(baseline, shots=shots)
        baseline_counts = baseline_job.result().get_counts()

        _eval_jobs[job_id]["progress"] = 0.7

        # Execute mitigated
        mitigated_job = simulator.run(mitigated_circuit, shots=shots)
        mitigated_counts = mitigated_job.result().get_counts()

        _eval_jobs[job_id]["progress"] = 0.9

        # Calculate fidelities (ideal would be noiseless)
        ideal_job = simulator.run(baseline, shots=shots)
        ideal_counts = ideal_job.result().get_counts()

        fid_baseline = hellinger_fidelity(
            baseline_counts, ideal_counts, shots, shots
        )
        fid_mitigated = hellinger_fidelity(
            mitigated_counts, ideal_counts, shots, shots
        )

        improvement = fid_mitigated - fid_baseline

        result = {
            "evaluation_id": job_id,
            "baseline": {
                "counts": baseline_counts,
                "shots": shots,
            },
            "mitigated": {
                "counts": mitigated_counts,
                "shots": shots,
            },
            "fidelity": {
                "baseline_fidelity": float(fid_baseline),
                "mitigated_fidelity": float(fid_mitigated),
                "improvement": float(improvement),
                "improvement_percent": float(improvement / fid_baseline * 100) if fid_baseline > 0 else 0,
            },
            "metrics": mit_metrics,
            "noise_tier": request.noise_tier.value,
        }

        _eval_jobs[job_id]["status"] = "completed"
        _eval_jobs[job_id]["result"] = result
        _eval_jobs[job_id]["progress"] = 1.0

        return result

    except Exception as e:
        _eval_jobs[job_id]["status"] = "failed"
        _eval_jobs[job_id]["error"] = str(e)
        raise


@router.post("/evaluate", response_model=JobStatus)
async def evaluate(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute baseline vs Q-Weave evaluation.

    Compares standard Qiskit transpilation against Q-Weave mitigated
    circuit on Aer simulator with synthetic noise.

    Returns a job ID for polling status.
    """
    job_id = f"eval_{uuid.uuid4().hex[:12]}"
    _eval_jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0.0,
        "created_at": datetime.now().isoformat(),
    }

    background_tasks.add_task(_run_evaluation_sync, job_id, request)

    return JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Evaluation job queued",
        created_at=_eval_jobs[job_id]["created_at"]
    )


@router.get("/evaluate/{job_id}/status", response_model=JobStatus)
async def get_evaluation_status(job_id: str):
    """Get status of an evaluation job."""
    if job_id not in _eval_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _eval_jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job.get("status", "unknown"),
        progress=job.get("progress"),
        message=job.get("message"),
        created_at=job.get("created_at"),
        completed_at=job.get("completed_at") if job.get("status") == "completed" else None
    )


@router.get("/evaluate/{job_id}/result", response_model=EvaluationResponse)
async def get_evaluation_result(job_id: str):
    """Get the result of a completed evaluation job."""
    if job_id not in _eval_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _eval_jobs[job_id]
    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job.get('status')}"
        )

    result = job.get("result", {})

    return EvaluationResponse(
        evaluation_id=result["evaluation_id"],
        baseline=ExecutionCounts(**result["baseline"]),
        mitigated=ExecutionCounts(**result["mitigated"]),
        fidelity=FidelityMetrics(**result["fidelity"]),
        metrics=MitigationMetrics(**result["metrics"]),
        noise_tier=result["noise_tier"]
    )


@router.get("/evaluate/{job_id}/counts")
async def get_execution_counts(job_id: str, top: int = 10):
    """Get top measurement counts from evaluation."""
    if job_id not in _eval_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _eval_jobs[job_id]
    result = job.get("result", {})

    baseline_counts = result.get("baseline", {}).get("counts", {})
    mitigated_counts = result.get("mitigated", {}).get("counts", {})

    # Sort by count
    sorted_baseline = sorted(
        baseline_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top]

    sorted_mitigated = sorted(
        mitigated_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top]

    return {
        "baseline_top": [
            {"bitstring": k, "count": v}
            for k, v in sorted_baseline
        ],
        "mitigated_top": [
            {"bitstring": k, "count": v}
            for k, v in sorted_mitigated
        ],
    }


@router.post("/evaluate/all-tiers")
async def evaluate_all_tiers(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks
):
    """
    Run evaluation across all three noise tiers.

    Returns aggregate results for comparison.
    """
    from qweave_api.models import NoiseTier

    tiers = [NoiseTier.HIGH, NoiseTier.MEDIUM, NoiseTier.LOW]

    job_ids = []
    for tier in tiers:
        tier_request = request.copy()
        tier_request.noise_tier = tier

        job_id = f"eval_{tier.value.lower()}_{uuid.uuid4().hex[:8]}"
        _eval_jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
        }

        background_tasks.add_task(_run_evaluation_sync, job_id, tier_request)
        job_ids.append({"tier": tier.value, "job_id": job_id})

    return {
        "message": "All tier evaluations queued",
        "jobs": job_ids,
    }
```

---

## Step 9: Router Package Init

**File:** `qweave_api/routers/__init__.py`

```python
"""API route modules."""

from qweave_api.routers import characterization
from qweave_api.routers import graph
from qweave_api.routers import mitigation
from qweave_api.routers import evaluation

__all__ = [
    "characterization",
    "graph",
    "mitigation",
    "evaluation",
]
```

---

## Step 10: Environment File Template

**File:** `.env.example`

```bash
# Q-Weave API Configuration

# Application
APP_NAME="Q-Weave API"
DEBUG=False

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=1

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Paths
RESULTS_DIR=./results
CACHE_DIR=./cache

# Execution defaults
DEFAULT_SHOTS=8192
MAX_SHOTS=65536

# Performance
REQUEST_TIMEOUT=300
MAX_CONCURRENT_JOBS=4
```

---

## Step 11: Testing the API

Create `tests/test_api.py`:

```python
"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from qweave_api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_benchmark_endpoint(client):
    """Test benchmark generation endpoint."""
    response = client.post("/api/benchmark", json={
        "benchmark_type": "GHZ",
        "num_qubits": 4,
        "noise_tier": "MEDIUM"
    })
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "qasm" in data
    assert data["num_qubits"] == 4


def test_characterize_job_creation(client):
    """Test characterization job creation."""
    response = client.post("/api/characterize", json={
        "circuit": {
            "num_qubits": 4,
            "name": "test"
        },
        "noise_tier": "LOW",
        "shots": 1024
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "job_id" in data


def test_invalid_noise_tier(client):
    """Test validation of noise tier."""
    response = client.post("/api/characterize", json={
        "circuit": {"num_qubits": 4},
        "noise_tier": "INVALID"
    })
    assert response.status_code == 422  # Validation error
```

---

## Phase 3 Completion Criteria

**This phase is complete when:**

1. FastAPI server starts without errors (`uvicorn qweave_api.main:app`)
2. All four API endpoint groups are functional:
   - `/api/characterize` - Run probe circuits, return interaction matrix
   - `/api/graph` - Return NetworkX nodes/edges for visualization
   - `/api/mitigate` - Run placement + greedy scheduler
   - `/api/evaluate` - Execute baseline vs Q-Weave on Aer
3. Pydantic models validate request/response data correctly
4. CORS is configured for frontend communication
5. Background job tracking works for long-running operations
6. State management persists characterization and mitigation results
7. API tests pass

---

## Running the API

```bash
# Development (with auto-reload)
cd /home/neonpulse/Dev/codezz/College/sem7/Qweave
source venv/bin/activate
uvicorn qweave_api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn qweave_api.main:app --host 0.0.0.0 --port 8000 --workers 1

# With environment file
ENV_FILE=.env.production uvicorn qweave_api.main:app
```

---

## API Documentation

Once running, access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Next Phase

Proceed to [04_frontend_ui_integration.md](./04_frontend_ui_integration.md) to implement the Next.js dashboard.
