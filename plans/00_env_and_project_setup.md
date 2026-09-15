# Phase 0: Environment and Project Setup

## Objective
Establish the complete development environment and monorepo structure for the Q-Weave quantum compiler framework. This phase creates the foundation upon which all subsequent phases depend.

---

## Prerequisites
- Python 3.10+ installed
- Node.js 18+ / npm 9+ (for Next.js frontend)
- Git configured

---

## Step 1: Repository Root Structure

Create the following directory structure at `/home/neonpulse/Dev/codezz/College/sem7/Qweave/`:

```
q-weave/
├── plans/                    # Master execution plans (this directory)
├── qweave/                   # Core compiler Python package
│   ├── __init__.py
│   ├── characterization/
│   ├── crosstalk_model/
│   ├── mitigation/
│   └── evaluation/
├── qweave_api/               # FastAPI backend
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   └── core/
├── qweave_ui/                # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
├── experiments/              # Benchmark and validation scripts
├── tests/                    # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/                     # Additional documentation
├── .gitignore
└── README.md
```

### Commands to execute:

```bash
# Create directory structure
mkdir -p qweave/{characterization,crosstalk_model,mitigation,evaluation}
mkdir -p qweave_api/{routers,core}
mkdir -p qweave_ui/{app,components,lib,public}
mkdir -p tests/{unit,integration}
mkdir -p experiments
mkdir -p docs
```

---

## Step 2: Python Virtual Environment

### 2.1 Create Virtual Environment

```bash
cd /home/neonpulse/Dev/codezz/College/sem7/Qweave
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2.2 Create requirements.txt

**File:** `requirements.txt`

```text
# Core Qiskit (spec-compliant versions)
qiskit>=1.0
qiskit-aer>=0.14

# Scientific computing
numpy>=1.24.0
scipy>=1.10.0

# Graph algorithms
networkx>=3.0

# API framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0

# Data validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0

# Development
black>=24.0.0
isort>=5.13.0
mypy>=1.8.0
flake8>=7.0.0

# Optional visualization
matplotlib>=3.8.0
plotly>=5.18.0
```

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.4 Verify Qiskit Installation

Create `tests/test_qiskit_import.py`:

```python
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
```

Run verification:
```bash
pytest tests/test_qiskit_import.py -v
```

---

## Step 3: Core Package Initialization

### 3.1 qweave/__init__.py

```python
"""
Q-Weave: A Crosstalk-Aware Error Mitigation Framework for NISQ Circuits.

Core thesis: MEASURE -> MODEL -> MITIGATE -> EXECUTE -> EVALUATE
"""

__version__ = "0.1.0"
__author__ = "Q-Weave Team"

from qweave.characterization.profiler import CrosstalkProfiler
from qweave.crosstalk_model.graph import CrosstalkGraph
from qweave.mitigation.engine import MitigationEngine

__all__ = [
    "CrosstalkProfiler",
    "CrosstalkGraph",
    "MitigationEngine",
]
```

### 3.2 Package Submodule Inits

Create empty `__init__.py` files in all subpackages:

```bash
touch qweave/characterization/__init__.py
touch qweave/crosstalk_model/__init__.py
touch qweave/mitigation/__init__.py
touch qweave/evaluation/__init__.py
touch qweave_api/__init__.py
touch qweave_api/routers/__init__.py
```

---

## Step 4: Configure Package Installation

### 4.1 Create pyproject.toml

**File:** `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "qweave"
version = "0.1.0"
description = "Crosstalk-Aware Error Mitigation Framework for NISQ Circuits"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Q-Weave Team"}
]
keywords = ["quantum", "crosstalk", "mitigation", "qiskit", "compiler"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Physics",
]
dependencies = [
    "qiskit>=1.0",
    "qiskit-aer>=0.14",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "networkx>=3.0",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "isort>=5.13.0",
    "mypy>=1.8.0",
    "flake8>=7.0.0",
]
viz = [
    "matplotlib>=3.8.0",
    "plotly>=5.18.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["qweave*", "qweave_api*"]
exclude = ["tests*", "experiments*", "qweave_ui*"]

[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short"
asyncio_mode = "auto"
```

### 4.2 Install Package in Editable Mode

```bash
pip install -e ".[dev,viz]"
```

---

## Step 5: Git Configuration

### 5.1 Create .gitignore

**File:** `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Jupyter Notebooks
.ipynb_checkpoints

# Environment variables
.env
.env.local

# Testing
.pytest_cache/
.coverage
htmlcov/

# Database files
*.db
*.sqlite
*.sqlite3

# Q-Weave specific
qweave_results/
profiling_data/
simulation_cache/

# Node.js (for frontend)
node_modules/
dist/
.next/
out/

# OS
.DS_Store
Thumbs.db
```

---

## Step 6: Frontend Setup (Next.js)

### 6.1 Initialize Next.js Project

```bash
cd qweave_ui
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-npm
```

### 6.2 Install Additional Dependencies

```bash
npm install @tanstack/react-query axios recharts lucide-react clsx tailwind-merge
```

### 6.3 Update tailwind.config.ts

Extend the configuration with the Q-Weave design system colors:

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Q-Weave Quantum Synthetic Design System
        background: '#0b1326',
        surface: {
          DEFAULT: '#0b1326',
          dim: '#0b1326',
          bright: '#31394d',
          variant: '#2d3449',
        },
        'surface-container': {
          lowest: '#060e20',
          low: '#131b2e',
          DEFAULT: '#171f33',
          high: '#222a3d',
          highest: '#2d3449',
        },
        primary: {
          DEFAULT: '#8aebff',
          fixed: '#a2eeff',
          dim: '#2fd9f4',
          container: '#22d3ee',
        },
        secondary: {
          DEFAULT: '#d0bcff',
          fixed: '#e9ddff',
          dim: '#d0bcff',
          container: '#571bc1',
        },
        tertiary: {
          DEFAULT: '#ffd6a3',
          fixed: '#ffddb5',
          dim: '#ffb957',
          container: '#ffb13b',
        },
        error: {
          DEFAULT: '#ffb4ab',
          container: '#93000a',
        },
        outline: {
          DEFAULT: '#859397',
          variant: '#3c494c',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'data-lg': ['20px', { lineHeight: '28px', fontWeight: '500' }],
        'data-md': ['14px', { lineHeight: '20px', fontWeight: '500' }],
        'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.1em', fontWeight: '700' }],
      },
      spacing: {
        unit: '4px',
        gutter: '24px',
        margin: '32px',
        'container-padding': '20px',
      },
      backdropBlur: {
        '2xl': '16px',
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## Step 7: Testing Framework Setup

### 7.1 Create conftest.py

**File:** `tests/conftest.py`

```python
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
```

### 7.2 Create Mock Backends for Testing

**File:** `tests/mock_backends.py`

```python
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
```

---

## Step 8: Verification Checklist

After completing this phase, verify:

- [ ] `venv/` directory exists and is active
- [ ] `pip list` shows qiskit>=1.0 and qiskit-aer>=0.14
- [ ] `pytest tests/test_qiskit_import.py` passes
- [ ] `python -c "import qweave"` succeeds
- [ ] `python -c "import qweave_api"` succeeds
- [ ] `qweave_ui/` contains Next.js structure with node_modules/
- [ ] Git repository is initialized with proper .gitignore
- [ ] All __init__.py files are in place

---

## Phase 0 Completion Criteria

**This phase is complete when:**

1. Python virtual environment is created and activated
2. All dependencies from requirements.txt are installed
3. Qiskit and Aer imports work correctly
4. Package structure is initialized with __init__.py files
5. pyproject.toml is configured for editable install
6. Frontend Next.js project is initialized with proper styling
7. Test framework is set up with fixtures and mock backends
8. All verification checklist items pass

---

## Next Phase

Proceed to [01_core_compiler_engine.md](./01_core_compiler_engine.md) to implement the characterization, modeling, and mitigation components.
