# Q-Weave Development Guide

This guide enables stateless session continuity for the Q-Weave quantum compiler project.

**CRITICAL**: Each session starts fresh with no context. This file, `/logs/completed.md`, and `/plans/` are the ONLY sources of truth.

---

## Session Startup Protocol

**ALWAYS run this at the start of every session:**

```bash
# 1. Read the master plan index
Read /home/neonpulse/Dev/codezz/College/sem7/Qweave/plans/README.md

# 2. Read what has been completed
Read /home/neonpulse/Dev/codezz/College/sem7/Qweave/logs/completed.md

# 3. Determine next task based on plan status vs completed work
```

---

## Directory Structure

```
q-weave/
├── plans/                    # MASTER PLANS - read-only reference
│   ├── README.md            # Phase index, status, and quick reference
│   ├── 00_env_and_project_setup.md
│   ├── 01_core_compiler_engine.md
│   ├── 02_validation_and_benchmarks.md
│   ├── 03_fastapi_backend.md
│   ├── 04_frontend_ui_integration.md
│   └── 05_documentation_and_deliverables.md
│
├── logs/                     # SESSION LOG - append only
│   └── completed.md         # What has been finished (you write here)
│
├── Frontend-prototype/       # UI REFERENCE - read-only
│   ├── quantum_synthetic/   # Design tokens, colors, CSS variables
│   ├── hardware_model_q_weave_engine/      # Hardware tab components
│   ├── compiler_optimization_q_weave_engine/ # Compiler tab components
│   └── evaluation_metrics_q_weave_engine/   # Evaluation tab components
│
├── qweave/                   # IMPLEMENT: Core Python package
├── qweave_api/               # IMPLEMENT: FastAPI backend
├── qweave_ui/                # IMPLEMENT: Next.js frontend
├── experiments/              # IMPLEMENT: Benchmark scripts
└── tests/                    # IMPLEMENT: Test suite
```

---

## Quick Reference

### Phase Sequence
1. Phase 0: Environment Setup
2. Phase 1: Core Compiler Engine
3. Phase 2: Validation & Benchmarks
4. Phase 3: FastAPI Backend
5. Phase 4: Frontend UI
6. Phase 5: Documentation

### Core Pipeline
```
MEASURE → MODEL → MITIGATE → EXECUTE → EVALUATE
```

### Critical Parameters

| Parameter | Value |
|-----------|-------|
| Shots per probe | 8,192 |
| Seed repeats | 5 |
| Max 2-Opt iterations | 200 |
| Coupling topology | 3×3 grid (9 qubits) |

### Noise Tiers
| Tier | Depolarizing p |
|------|----------------|
| HIGH | 0.15 |
| MEDIUM | 0.07 |
| LOW | 0.02 |

### Cost Function Weights
```
cost = 1.0·depth + 0.5·gates + 2.0·error + 5.0·crosstalk
```

### Validation Criterion
Mitigated fidelity > baseline + 2×SE in ≥2 of 3 noise tiers

---

## Frontend Reference (Frontend-prototype/)

Read these for design patterns:
- `quantum_synthetic/globals.css` - Design tokens (colors, spacing, typography)
- `hardware_model_q_weave_engine/` - Hardware visualization components
- `compiler_optimization_q_weave_engine/` - Compiler interface components
- `evaluation_metrics_q_weave_engine/` - Charts and metrics display

### Key Design Tokens
- Background: `#0b1326` (deep slate)
- Surface Container High: `#222a3d`
- Primary (Cyan): `#8aebff`
- Secondary (Violet): `#d0bcff`
- Tertiary (Amber): `#ffd6a3`
- Error: `#ffb4ab`

---

## Completion Logging

When you finish work, APPEND to `/logs/completed.md`:

```markdown
## YYYY-MM-DD HH:MM - Brief description

### Completed
- [x] Specific task 1
- [x] Specific task 2

### Files Created/Modified
- `path/to/file.py` - What it does
- `path/to/file.ts` - What it does

### Verification Commands Run
```bash
pytest tests/unit/test_file.py -v
python -c "import qweave; print('OK')"
```

### Notes
- Important context for future sessions
- Known issues or blockers
- Next steps when resuming
```

---

## Implementation Rules

1. **NEVER modify `/plans/`** - These are read-only reference
2. **ONLY append to `/logs/completed.md`** - Never delete or overwrite
3. **Use `/Frontend-prototype/` as reference** - Copy/adapt patterns, don't modify
4. **Verify before claiming complete** - Run tests, check imports
5. **Follow plan documents exactly** - Match function signatures, formulas, algorithms

---

## Common Verification Commands

```bash
# Python package import
python -c "from qweave.characterization.profiler import CrosstalkProfiler; print('OK')"

# Run tests
pytest tests/ -v --tb=short

# Start backend
cd qweave_api && uvicorn main:app --reload

# Start frontend
cd qweave_ui && npm run dev

# Quick benchmark
python experiments/quick_validate.py --circuit GHZ --noise medium
```
