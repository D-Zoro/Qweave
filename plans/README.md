# Q-Weave Master Execution Plan

## Project Overview
**Q-Weave: An Empirical Framework for Crosstalk-Aware Error Mitigation in NISQ Quantum Circuits**

This directory contains the complete, exhaustive step-by-step master execution plan for implementing the Q-Weave quantum compiler framework. The plan follows the core thesis: **MEASURE → MODEL → MITIGATE → EXECUTE → EVALUATE**.

---

## Phase Index

| Phase | Document | Status | Description |
|-------|----------|--------|-------------|
| 0 | [00_env_and_project_setup.md](./00_env_and_project_setup.md) | ⏳ Pending | Environment, dependencies, monorepo layout |
| 1 | [01_core_compiler_engine.md](./01_core_compiler_engine.md) | ⏳ Pending | Characterization, crosstalk model, placement, scheduling |
| 2 | [02_validation_and_benchmarks.md](./02_validation_and_benchmarks.md) | ⏳ Pending | Synthetic noise tiers, validation criteria, benchmarks |
| 3 | [03_fastapi_backend.md](./03_fastapi_backend.md) | ⏳ Pending | REST API, Pydantic models, async endpoints |
| 4 | [04_frontend_ui_integration.md](./04_frontend_ui_integration.md) | ⏳ Pending | Next.js dashboard, glassmorphism UI, visualizations |
| 5 | [05_documentation_and_deliverables.md](./05_documentation_and_deliverables.md) | ⏳ Pending | README, benchmark scripts, panel defense guide |

---

## Execution Status Legend

- ⏳ **Pending**: Plan drafted, awaiting implementation
- 🔄 **In Progress**: Currently being implemented
- ✅ **Complete**: Phase finished and verified
- 🚫 **Blocked**: Waiting on dependencies

---

## Critical Dependencies & Constraints

1. **Backend Prerequisites**: Phase 0 and Phase 1 MUST be complete before Phase 2 validation
2. **API Prerequisites**: Phase 1 and Phase 2 MUST pass before Phase 3 API development
3. **UI Prerequisites**: Phase 3 API MUST be functional before Phase 4 frontend integration
4. **Documentation**: Phase 5 can proceed in parallel with Phase 4

---

## Quick Reference: Key Technical Specifications

### Fixed Noise Tiers
| Label | Extra Depolarizing Probability |
|-------|-------------------------------|
| HIGH | 0.15 |
| MEDIUM | 0.07 |
| LOW | 0.02 |

### Execution Parameters
- **Shots per probe**: 8,192
- **Seed repeats**: 5
- **Max 2-opt iterations**: 200
- **Coupling topology**: 3×3 grid (fixed for comparability)

### Cost Function Weights
```
cost = 1.0·depth_term + 0.5·gate_term + 2.0·error_term + 5.0·crosstalk_term
```

### Success Threshold (Level 2)
Mitigated fidelity must exceed baseline by > 2× SE in ≥ 2 out of 3 noise tiers.

---

## Repository Structure (Target)

```
q-weave/
├── plans/                    # This directory - master execution plans
├── qweave/                   # Core compiler package
│   ├── characterization/
│   ├── crosstalk_model/
│   ├── mitigation/
│   └── evaluation/
├── qweave_api/               # FastAPI backend
│   ├── main.py
│   ├── models.py
│   └── routers/
├── qweave_ui/                # Next.js frontend
│   ├── app/
│   ├── components/
│   └── lib/
├── experiments/              # Benchmark scripts
├── tests/                    # Test suite
└── README.md
```

---

## Panel Defense Summary

**One-Sentence Summary:**
> Q-Weave empirically discovers execution-dependent crosstalk, models those interactions as a weighted hardware graph, and uses the model for software-level error mitigation through crosstalk-aware qubit placement and scheduling, with Qiskit/Aer used as the experimental platform.

**Key Q&A Responses:**
- **"Is this just scheduling?"** → No, scheduling is one mitigation layer. The framework includes characterization, interaction modeling, and both placement + scheduling.
- **"Is this error correction?"** → No, it's error mitigation at the compilation level, not quantum error correction.
- **"Where is the AI?"** → The MVP uses empirical measurements and optimization heuristics. ML is a future extension.
- **"Does your algorithm guarantee the best schedule?"** → No, the MVP uses a crosstalk-aware greedy heuristic; it does not guarantee global optimum.
- **"Why would you increase circuit depth?"** → Minimizing depth alone can increase crosstalk. Serializing strongly-interacting operations may increase depth but reduce execution error.

---

## Implementation Checklist

- [ ] Phase 0: Environment and project setup complete
- [ ] Phase 1: Core compiler engine functional
- [ ] Phase 2: Level 1 and Level 2 validation passing
- [ ] Phase 3: FastAPI backend with all endpoints
- [ ] Phase 4: Next.js frontend with all three tabs
- [ ] Phase 5: Documentation and deliverables complete

---

## Notes

- This plan follows the exact project specification in `Q-Weave_Exact_Project_Specification_for_Claude(1).md`
- The frontend UI prototype is located at `./Frontend-prototype/` and will be adapted during Phase 4
- All mathematical formulas, statistical estimators, and normalized cost functions are defined in the specification
- **Do NOT write application source code until all plan documents are reviewed and approved**
