# Q-Weave --- Exact Project Specification for Claude

## 1. Project identity

**Project name:** Q-Weave

**Recommended title:**

> **Q-Weave: An Empirical Framework for Crosstalk-Aware Error Mitigation
> in NISQ Quantum Circuits**

### Important positioning

Q-Weave should **NOT** be presented primarily as a "Qiskit extension" or
"Qiskit plugin."

The core project is:

> **A crosstalk-aware error-mitigation framework for quantum circuit
> execution.**

Qiskit and Qiskit Aer are the **implementation and demonstration
platform** used to build and evaluate the framework.

The project is a **quantum software / compiler / error-mitigation
engineering project**, not a new quantum algorithm, not an AI project,
and not a hardware-control project.

------------------------------------------------------------------------

# 2. The problem being solved

Quantum processors, especially noisy intermediate-scale quantum (NISQ)
processors, do not necessarily experience the same error when gates
execute individually versus when multiple gates execute simultaneously.

For example:

``` text
CX(q0, q1)
```

may have relatively good fidelity when executed alone.

But:

``` text
CX(q0, q1) || CX(q2, q3)
```

may have substantially worse fidelity because the simultaneous
operations can interact through unwanted physical effects.

This is **crosstalk**.

The key observation is:

``` text
Error(gate)
    !=
Error(gate | other operations executing concurrently)
```

Therefore, isolated gate-error information is not always enough to
predict the quality of an entire circuit execution.

A circuit schedule that looks optimal because it maximizes parallelism
may actually produce worse results because some parallel operations
strongly interfere with each other.

------------------------------------------------------------------------

# 3. The central research question

The core research question is:

> **Can execution-dependent crosstalk be empirically characterized and
> exploited to mitigate crosstalk-induced errors in quantum circuit
> execution?**

A more specific version is:

> **Can empirically derived crosstalk information improve the fidelity
> of NISQ quantum circuits through crosstalk-aware qubit placement and
> scheduling?**

The hypothesis is:

> If crosstalk-induced error depends on which operations execute
> concurrently, then identifying high-interaction operation pairs and
> avoiding or reducing their simultaneous execution should reduce
> execution error and improve circuit fidelity, at the cost of
> potentially increased circuit depth.

------------------------------------------------------------------------

# 4. What Q-Weave actually does

The complete pipeline is:

``` text
Quantum Circuit
      |
      v
Crosstalk Characterization
      |
      v
Measured Execution-Dependent Interactions
      |
      v
Crosstalk Interaction Model
      |
      v
Weighted Interaction Graph
      |
      +-----------------------+
      |                       |
      v                       v
Qubit Placement          Gate Scheduling
      |                       |
      +-----------+-----------+
                  |
                  v
        Crosstalk-Mitigated Circuit
                  |
                  v
             Qiskit / Aer
                  |
                  v
              Execution
                  |
                  v
             Evaluation
```

The project therefore follows:

> **MEASURE -\> MODEL -\> MITIGATE -\> EXECUTE -\> EVALUATE**

------------------------------------------------------------------------

# 5. What "error mitigation" means here

Q-Weave is **not quantum error correction**.

It does not encode logical qubits into large numbers of physical qubits
and does not correct errors using a quantum error-correcting code.

Q-Weave performs **software-level / compilation-level error
mitigation**.

The idea is:

``` text
Detect configurations that cause additional crosstalk
                    |
                    v
Change how the circuit is executed
                    |
                    v
Reduce exposure to those configurations
                    |
                    v
Reduce observed execution error
```

The primary mitigation mechanisms are:

1.  **Crosstalk-aware qubit placement / mapping**
2.  **Crosstalk-aware gate scheduling**

Scheduling is therefore only **one component** of the mitigation
framework.

An optional future/advanced component is **crosstalk-aware randomized
compiling**, but this should not be a mandatory MVP dependency unless
implementation time permits.

------------------------------------------------------------------------

# 6. Why this is not just a scheduling project

A weak description would be:

> "We find bad gate pairs and execute them one after another."

That is only one part of Q-Weave.

The complete framework is:

``` text
1. Characterize crosstalk experimentally
2. Infer interaction strengths
3. Build a hardware-specific interaction model
4. Use the model for physical qubit placement
5. Use the model for execution scheduling
6. Execute the resulting circuit
7. Compare error/fidelity against baseline
```

The contribution is therefore the **empirical characterization -\>
interaction modeling -\> multi-stage mitigation -\> evaluation
pipeline**.

The project does NOT claim that crosstalk-aware compilation itself is a
new research area. Existing work already studies crosstalk
characterization, mapping, scheduling, pulse-level mitigation,
randomized compiling, and related techniques.

The intended contribution is an integrated, reproducible student-level
framework that combines these concepts into a single experimentally
testable workflow.

------------------------------------------------------------------------

# 7. Qiskit's role

Qiskit is the **experimental platform**, not the identity of the
research problem.

Qiskit provides:

-   `QuantumCircuit`
-   circuit construction
-   transpilation infrastructure
-   circuit representations
-   execution interfaces
-   access to Aer
-   optional access to real quantum backends

Q-Weave provides the project-specific logic:

-   crosstalk characterization
-   interaction estimation
-   crosstalk graph construction
-   crosstalk-aware placement
-   crosstalk-aware scheduling
-   evaluation of mitigation effectiveness

Conceptually:

``` text
Qiskit QuantumCircuit
        |
        v
      Q-Weave
        |
        +--> Characterization
        |
        +--> Crosstalk Model
        |
        +--> Placement
        |
        +--> Scheduling
        |
        v
Mitigated Qiskit-compatible Circuit
        |
        v
Qiskit Aer / optional QPU
```

Do NOT describe the project as merely "a Qiskit plugin."

------------------------------------------------------------------------

# 8. Qiskit Aer and the crosstalk simulation

Qiskit Aer does **not** provide a magical built-in universal "crosstalk
simulator."

Instead, Q-Weave will use Aer to create a **controlled synthetic
correlated-noise environment** that reproduces the execution-dependent
behavior needed for the experiment.

For example, the simulator may contain a hidden rule such as:

``` text
IF CX(q0,q1) and CX(q2,q3)
execute concurrently

THEN introduce additional correlated error
```

Crucially:

> **The profiler must NOT be given this hidden rule.**

The hidden rule belongs to the synthetic environment.

Q-Weave only observes the outcomes of its probe circuits.

This allows the project to test whether the framework can **discover**
crosstalk from measurements rather than simply reading a hardcoded
answer.

The synthetic model is a controlled experimental abstraction. It is NOT
claimed to reproduce the complete microwave-level physics of an IBM or
other commercial quantum processor.

------------------------------------------------------------------------

# 9. Crosstalk characterization

The profiler generates probe circuits.

For two candidate operations:

``` text
A = CX(q0,q1)
B = CX(q2,q3)
```

run at least:

### Probe 1 --- A individually

``` text
CX(q0,q1)
```

### Probe 2 --- B individually

``` text
CX(q2,q3)
```

### Probe 3 --- A and B concurrently

``` text
CX(q0,q1) || CX(q2,q3)
```

Suppose:

``` text
A alone       -> 98.5% fidelity
B alone       -> 98.2% fidelity
A || B        -> 87.1% fidelity
```

The large degradation under concurrent execution indicates a strong
execution-dependent interaction.

The exact statistical estimator is an implementation decision and must
be chosen carefully. The framework should not assume that every fidelity
difference is automatically pure crosstalk; the estimator should account
for the baseline error of the individual operations.

------------------------------------------------------------------------

# 10. Interaction estimation

The profiler converts measurements into an interaction score.

Conceptually:

``` text
interaction(A,B)
    =
additional degradation caused by concurrent execution
```

The exact formula is intentionally not hardcoded in this project
specification.

A practical implementation could derive a normalized interaction score
from:

-   isolated execution error
-   concurrent execution error
-   repeated measurements/shots
-   statistical uncertainty

The important requirement is:

> **The interaction score must be derived from observed probe outcomes
> rather than directly copied from the hidden simulator rule.**

------------------------------------------------------------------------

# 11. Interaction matrix

The measured interactions can first be stored as a matrix.

Example:

``` text
             A       B       C       D
A            -      0.90    0.05    0.10
B           0.90     -      0.08    0.20
C           0.05    0.08     -      0.03
D           0.10    0.20    0.03     -
```

Interpretation:

``` text
A-B = strong interaction
A-C = weak interaction
B-D = moderate interaction
```

This is a data representation of observed execution-context dependence.

------------------------------------------------------------------------

# 12. Crosstalk interaction graph

The matrix can be represented as a weighted graph:

``` text
             0.90
        A ------------ B
        |              |
      0.05           0.20
        |              |
        C ------------ D
             0.03
```

Mathematically:

``` text
G_XT = (V, E, W)
```

where:

-   `V` = physical qubits or relevant operation locations
-   `E` = potentially interacting pairs
-   `W(e)` = estimated crosstalk/interference severity

The graph is the bridge between **experimental measurement** and
**compiler decisions**.

------------------------------------------------------------------------

# 13. Mitigation mechanism 1 --- Crosstalk-aware placement

The graph can influence logical-to-physical qubit mapping.

Suppose logical operations that frequently interact are likely to
execute together.

If a particular physical region has strong crosstalk:

``` text
physical region:
q0 -- q1
 \    /
 HIGH interaction
```

Q-Weave can try to avoid mapping strongly interacting logical operations
into that problematic configuration.

Conversely, it can prefer physical locations with lower measured
interaction.

This makes the framework broader than simple scheduling.

Important:

> Placement optimization must remain practical for the MVP. It does not
> need to become a globally optimal combinatorial optimizer.

------------------------------------------------------------------------

# 14. Mitigation mechanism 2 --- Crosstalk-aware scheduling

After placement, the scheduler considers which ready operations should
execute in the same layer.

Example:

``` text
A = CX(q0,q1)
B = CX(q2,q3)
```

If:

``` text
W(A,B) = HIGH
```

then the scheduler should avoid:

``` text
Layer 1: A B
```

and may choose:

``` text
Layer 1: A
Layer 2: B
```

If:

``` text
W(A,B) = LOW
```

then parallel execution remains desirable:

``` text
Layer 1: A B
```

The objective is NOT:

> minimize crosstalk at any cost.

The objective is:

> **find a good tradeoff between execution fidelity, crosstalk exposure,
> circuit depth, and gate cost.**

------------------------------------------------------------------------

# 15. Scheduling algorithm for the MVP

The project should begin with a **crosstalk-aware greedy/list-scheduling
heuristic**.

Do NOT begin with MaxSAT or a complicated exact optimizer.

At each scheduling step:

1.  Identify operations whose dependencies are satisfied.
2.  Create the current execution layer.
3.  Select a feasible candidate operation.
4.  Determine which other ready operations can execute concurrently.
5.  Calculate the incremental cost of adding a candidate to the current
    layer.
6.  Prefer the candidate that gives the lowest incremental cost.
7.  Continue filling the layer.
8.  Start a new layer when appropriate.
9.  Repeat until all operations are scheduled.

The conceptual cost function is:

``` text
C =
    alpha  * circuit_depth
  + beta   * two_qubit_gate_count
  + gamma  * estimated_gate_error
  + lambda * crosstalk_penalty
```

For concurrent operations:

``` text
crosstalk_penalty
    = sum of interaction weights
```

over relevant operation pairs executing in the same layer.

### Important algorithmic claim

The greedy heuristic does **NOT** guarantee a globally optimal schedule.

It finds a low-cost schedule efficiently.

Do not claim:

> "We calculate the mathematically best possible sequence."

Instead say:

> "The MVP uses a crosstalk-aware greedy scheduling heuristic to
> efficiently find a low-cost execution schedule."

------------------------------------------------------------------------

# 16. Optional advanced optimizer

If the basic implementation works early, a second search method can be
added for comparison.

A good candidate is **beam search**.

Conceptually:

``` text
Current partial schedule
       |
   +---+---+---+
   A   B   C   D
   |   |   |   |
   v   v   v   v
candidate schedules
       |
       v
keep best K
       |
       v
expand again
```

This allows comparison:

``` text
Qiskit baseline
vs
Greedy Q-Weave
vs
Beam-search Q-Weave
```

This is optional.

Do not make advanced search a prerequisite for the MVP.

------------------------------------------------------------------------

# 17. Optional mitigation technique --- randomized compiling

A possible advanced extension is **crosstalk-aware randomized
compiling**.

This is conceptually different from scheduling.

Scheduling:

``` text
avoid the bad configuration
```

Randomized compiling:

``` text
randomize the coherent error behavior
while preserving the logical computation
```

The general workflow is:

``` text
Original circuit
      |
      v
Insert logically cancelling random transformations
      |
      v
Equivalent randomized circuits
      |
      v
Repeated execution
      |
      v
Average / reconstruct result
```

This should be treated as an optional extension, not a mandatory MVP
component.

If implemented, it gives Q-Weave a second fundamentally different
mitigation mechanism.

------------------------------------------------------------------------

# 18. What Q-Weave is NOT

The MVP does NOT require:

-   a custom quantum processor
-   microwave hardware
-   pulse-control electronics
-   exact physical simulation of a commercial QPU
-   a complete compiler from scratch
-   127-qubit global crosstalk characterization
-   machine learning
-   an LLM
-   AWS Braket
-   paid QPU access
-   real-time hardware calibration
-   MaxSAT as the first optimization method

The project should first prove:

``` text
measure
   ->
model
   ->
mitigate
   ->
execute
   ->
evaluate
```

------------------------------------------------------------------------

# 19. Baseline comparison

Every experiment must compare:

``` text
Standard Qiskit compilation
            VS
Q-Weave mitigation
```

using:

-   the same logical circuit
-   the same simulated hardware
-   the same noise environment
-   comparable execution shots
-   comparable evaluation conditions

Potential benchmark families:

-   GHZ
-   QAOA
-   QFT
-   random Clifford circuits
-   small VQE circuits

Do not rely on a single circuit.

------------------------------------------------------------------------

# 20. Evaluation metrics

### Primary metrics

#### Execution fidelity

Compare the observed output distribution against the ideal distribution.

Hellinger fidelity is one possible metric.

#### Success probability

For circuits with known expected outcomes:

``` text
P_success =
P(observed correct result)
```

### Secondary metrics

Measure:

-   circuit depth
-   two-qubit gate count
-   total error
-   crosstalk exposure
-   profiling time/cost
-   number of probe circuits
-   number of shots
-   compilation runtime

Profiling overhead is particularly important.

A mitigation method is less useful if it spends vastly more resources
characterizing the device than the improvement it provides.

------------------------------------------------------------------------

# 21. What counts as success?

A successful Q-Weave experiment should demonstrate all of the following:

### 1. Detection

The profiler identifies hidden synthetic crosstalk interactions from
measurements.

### 2. Modeling

The interactions are represented in a usable matrix/graph.

### 3. Mitigation

The compiler/scheduler changes execution decisions based on the graph.

### 4. Improvement

Under the controlled correlated-noise environment, the mitigated circuit
has lower execution error or higher fidelity than the baseline in
relevant conditions.

### 5. Tradeoff measurement

The experiment quantifies the cost of mitigation in terms of:

-   circuit depth
-   gate count
-   runtime
-   profiling overhead

There must be NO predetermined claim such as "Q-Weave improves fidelity
by 20%."

The actual experiments determine the improvement.

------------------------------------------------------------------------

# 22. Three experimental levels

## Level 1 --- Known synthetic crosstalk

Create one or a few simple hidden interactions.

Example:

``` text
CX(0,1) || CX(2,3)
        ->
additional error
```

Purpose:

> Validate that the characterization and mitigation pipeline works.

------------------------------------------------------------------------

## Level 2 --- Unknown synthetic crosstalk

Create several hidden interactions with different strengths:

``` text
(0,1) || (2,3) -> HIGH
(1,2) || (5,6) -> MEDIUM
(3,4) || (7,8) -> LOW
```

Do not expose these rules to Q-Weave.

Q-Weave must infer them from probe measurements.

This is the most important MVP experiment.

------------------------------------------------------------------------

## Level 3 --- Real hardware

Optional.

If freely available hardware access exists, use it as an additional
validation experiment.

The project must remain fully functional without real QPU access.

------------------------------------------------------------------------

# 23. Expected behavior

A plausible result pattern is:

``` text
Low crosstalk:
Baseline ~= Q-Weave

Medium crosstalk:
Q-Weave improves fidelity moderately

High crosstalk:
Q-Weave improves fidelity substantially
but may increase circuit depth
```

These are hypotheses/expected patterns, NOT guaranteed results.

The project must report the actual measured results.

------------------------------------------------------------------------

# 24. Important limitation

The synthetic Aer environment is a **controlled experimental model**,
not an exact representation of real quantum hardware.

Therefore the project should claim:

> "We demonstrate the effectiveness of the proposed mitigation pipeline
> under controlled execution-dependent correlated noise."

It should NOT claim:

> "We reproduce the exact crosstalk physics of IBM quantum processors."

Real hardware validation, if available, can strengthen the result.

------------------------------------------------------------------------

# 25. Scalability limitation

Full crosstalk characterization can become expensive as the number of
qubits and possible operation pairs increases.

Therefore:

``` text
number of qubits ↑
        |
possible interactions ↑
        |
probe circuits ↑
        |
profiling cost ↑
```

The MVP should use small controlled systems.

Future work could investigate:

-   sparse interaction graphs
-   local crosstalk assumptions
-   adaptive probing
-   selective characterization
-   graph sparsification
-   importance-based profiling
-   online/repeated recalibration

Do not pretend that exhaustive profiling scales trivially to large QPUs.

------------------------------------------------------------------------

# 26. Project architecture

Recommended repository:

``` text
q-weave/
│
├── qweave/
│   │
│   ├── characterization/
│   │   ├── probe_generator.py
│   │   ├── executor.py
│   │   └── estimator.py
│   │
│   ├── crosstalk_model/
│   │   ├── interaction_matrix.py
│   │   └── interaction_graph.py
│   │
│   ├── mitigation/
│   │   ├── cost_function.py
│   │   ├── placement.py
│   │   ├── scheduler.py
│   │   └── mitigation_engine.py
│   │
│   ├── evaluation/
│   │   ├── fidelity.py
│   │   ├── metrics.py
│   │   └── benchmarks.py
│   │
│   └── cli.py
│
├── experiments/
│   ├── synthetic_single_pair.py
│   ├── synthetic_multi_pair.py
│   └── benchmark.py
│
├── tests/
│
├── examples/
│
└── README.md
```

This is a suggested structure, not a rigid requirement.

------------------------------------------------------------------------

# 27. Technology stack

Core:

-   Python
-   Qiskit
-   Qiskit Aer
-   NumPy
-   SciPy
-   NetworkX
-   Matplotlib

Qiskit is the quantum circuit and transpilation platform.

Aer is the controlled simulation environment.

NetworkX is used for interaction graphs.

NumPy/SciPy support numerical/statistical calculations.

Matplotlib is used for visualizing interaction graphs and evaluation
results.

------------------------------------------------------------------------

# 28. What makes this a substantial final-year project?

The project contains several connected technical components:

``` text
Quantum circuit analysis
        +
Controlled noise simulation
        +
Experimental characterization
        +
Statistical interaction estimation
        +
Graph modeling
        +
Qubit placement
        +
Scheduling optimization
        +
Error mitigation
        +
Benchmarking
        +
Quantitative evaluation
```

It is therefore not simply:

> "write a scheduler."

The scheduler is one component of a broader empirical mitigation
pipeline.

------------------------------------------------------------------------

# 29. Novelty positioning

Do NOT claim:

> "We invented crosstalk-aware quantum compilation."

Do NOT claim:

> "Nobody has studied crosstalk-aware scheduling."

Do NOT claim:

> "We are the first to mitigate crosstalk."

Those areas already have substantial literature.

The defensible contribution is:

> **An integrated empirical framework that automatically characterizes
> execution-dependent crosstalk, converts measured interactions into a
> hardware-specific model, and uses that model for software-level
> mitigation through qubit placement and scheduling, with controlled
> simulation-based evaluation.**

Before making a formal claim that no identical implementation/product
exists, conduct a current search of:

-   recent papers
-   GitHub
-   PyPI
-   Qiskit packages
-   existing crosstalk-aware compiler implementations

The novelty claim should be about the **specific integrated
implementation and experimental workflow**, not the existence of the
underlying research area.

------------------------------------------------------------------------

# 30. Base-paper / literature positioning

The project should be grounded in several research pillars rather than
pretending one paper invented the whole idea.

### Pillar 1 --- Crosstalk characterization

Research establishing that simultaneous quantum operations can
experience additional errors compared with isolated execution.

### Pillar 2 --- Crosstalk-aware compilation

Research demonstrating that mapping, routing, scheduling and other
compilation decisions can account for crosstalk.

### Pillar 3 --- Crosstalk-specific error mitigation

Research using techniques such as randomized compiling or other
transformations to reduce crosstalk effects.

### Pillar 4 --- General quantum error mitigation

Research on methods such as zero-noise extrapolation, probabilistic
error cancellation and related techniques provides broader
error-mitigation context, but these are not automatically part of the
Q-Weave MVP.

Q-Weave combines relevant ideas into a controlled, student-buildable
empirical framework.

------------------------------------------------------------------------

# 31. Exact panel explanation

If asked:

> "Explain your project."

Use:

> **Quantum processors exhibit execution-dependent crosstalk, where a
> gate may have significantly different error when another gate executes
> simultaneously. Q-Weave is a crosstalk-aware error-mitigation
> framework designed to address this problem. We first characterize the
> hardware's execution-dependent interactions using individual and
> concurrent probe circuits. From the observed measurements, we estimate
> interaction strengths and construct a weighted crosstalk graph. This
> model is then used to influence physical qubit placement and gate
> scheduling, so operations with strong measured interactions are less
> likely to be executed in harmful configurations. We evaluate the
> resulting mitigated circuits against standard compilation under the
> same controlled correlated-noise environment using Qiskit Aer. Qiskit
> is the implementation and demonstration platform; the core
> contribution is the empirical characterization, interaction modeling
> and mitigation pipeline.**

------------------------------------------------------------------------

# 32. Exact answer if asked "Is this just scheduling?"

> **No. Scheduling is one mitigation layer. The framework first
> empirically characterizes execution-dependent crosstalk, constructs a
> hardware-specific interaction model, and can use that model for both
> physical qubit placement and gate scheduling. The optional advanced
> direction is randomized compiling, which mitigates coherent error
> through a fundamentally different mechanism.**

------------------------------------------------------------------------

# 33. Exact answer if asked "Is this error correction?"

> **No. It is error mitigation, not quantum error correction. We do not
> encode logical qubits or correct errors after they occur. We reduce
> the expected error by changing how the circuit is mapped and executed
> under known crosstalk characteristics.**

------------------------------------------------------------------------

# 34. Exact answer if asked "Where is the AI?"

> **There is no AI requirement. The MVP uses empirical measurements,
> statistical estimation, graph modeling and optimization heuristics.
> Machine learning could be a future extension, but it is intentionally
> not required for the core system.**

------------------------------------------------------------------------

# 35. Exact answer if asked "Why Qiskit?"

> **Qiskit gives us the quantum circuit representation, transpilation
> infrastructure and simulation environment needed to implement and
> demonstrate the framework. The research problem itself is
> crosstalk-aware error mitigation, not development of a Qiskit
> plugin.**

------------------------------------------------------------------------

# 36. Exact answer if asked "Can Qiskit simulate real crosstalk?"

> **Qiskit Aer does not automatically reproduce the full physical
> crosstalk behavior of a real processor. We construct a controlled
> synthetic correlated-noise model using Aer so that we can test whether
> our profiler can discover execution-dependent interactions and whether
> our mitigation strategy can exploit them. Real hardware validation is
> optional.**

------------------------------------------------------------------------

# 37. Exact answer if asked "Does your algorithm guarantee the best schedule?"

> **No. The MVP uses a crosstalk-aware greedy/list-scheduling heuristic
> to efficiently find a low-cost schedule. It does not guarantee the
> global optimum. An exact optimizer or beam-search comparison can be
> investigated as an extension.**

------------------------------------------------------------------------

# 38. Exact answer if asked "Why would you increase circuit depth?"

> **Because minimizing depth alone can increase crosstalk. If two
> operations have strong measured interaction, serializing them may
> increase depth but reduce execution error. Q-Weave therefore optimizes
> a tradeoff between depth, gate cost, estimated error and crosstalk
> exposure.**

------------------------------------------------------------------------

# 39. Exact answer if asked "What is your actual contribution?"

> **Our contribution is the integrated workflow: empirically
> characterize execution-dependent crosstalk, infer a usable interaction
> model, use that model for crosstalk-aware placement and scheduling,
> and quantitatively evaluate whether this reduces execution error under
> controlled correlated noise.**

------------------------------------------------------------------------

# 40. The one diagram to remember

``` text
                  QUANTUM CIRCUIT
                        |
                        v
              +-------------------+
              | CROSSTALK         |
              | CHARACTERIZATION  |
              +---------+---------+
                        |
                 probe circuits
                        |
                        v
                  MEASUREMENTS
                        |
                        v
              +-------------------+
              | CROSSTALK         |
              | INTERACTION MODEL |
              +---------+---------+
                        |
                        v
                WEIGHTED GRAPH
                        |
             +----------+----------+
             |                     |
             v                     v
       QUBIT PLACEMENT       GATE SCHEDULING
             |                     |
             +----------+----------+
                        |
                        v
              MITIGATED CIRCUIT
                        |
                        v
                 QISKIT / AER
                        |
                        v
                    RESULTS
                        |
                        v
            +---------------------+
            | Fidelity / Error    |
            | Depth / Gate Count  |
            | XT Exposure / Cost  |
            +---------------------+
```

------------------------------------------------------------------------

# 41. The project's core sentence

If Claude needs one sentence to keep the entire project consistent:

> **Q-Weave empirically discovers execution-dependent crosstalk, models
> those interactions as a weighted hardware graph, and uses the model
> for software-level error mitigation through crosstalk-aware qubit
> placement and scheduling, with Qiskit/Aer used as the experimental
> platform.**

That is the exact project scope.


# 42. Web UI and API Architecture (Presentation Layer)

The core specification focuses on the compiler backend, but the MVP must include a presentation layer to visually demonstrate the crosstalk-mitigation pipeline. This transforms the project from a command-line script into an interactive research and telemetry dashboard.

Recommended Tech Stack
A decoupled architecture ensures the heavy quantum simulation doesn't freeze the user interface.

Backend API: FastAPI handles asynchronous routing, triggers the Qiskit transpilation passes, and runs the Aer simulations efficiently.
Frontend UI: Next.js paired with Tailwind CSS provides the structure for a sleek, responsive, and dark-themed telemetry dashboard.
Data Visualization: The Python backend generates NetworkX graphs, which are passed to the frontend and rendered using interactive libraries like D3 or vis.js.
Core API Endpoints
The FastAPI server acts as the bridge between the Q-Weave compiler and the Next.js dashboard, exposing specific routes for each step of the pipeline.

POST /api/characterize: Accepts a target benchmark circuit and synthetic noise parameters, returning the calculated interaction matrix.
GET /api/graph: Fetches the weighted crosstalk graph data (nodes and penalty edges) for real-time frontend visualization.
POST /api/mitigate: Triggers the crosstalk-aware greedy scheduling heuristic and returns the modified JSON representation of the circuit.
POST /api/evaluate: Executes both the standard baseline and mitigated circuits in the controlled noise environment, returning comparative fidelity metrics.
Updated Repository Structure
To support the full-stack deployment, the repository architecture should be expanded to isolate the web layers from the core compiler.

qweave_api/: Contains the FastAPI application, route controllers, and Pydantic validation models.
qweave_ui/: Contains the Next.js frontend, layout components, state management, and charting modules.

# 43. Design.md
---
name: Quantum Synthetic
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bbc9cd'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#859397'
  outline-variant: '#3c494c'
  surface-tint: '#2fd9f4'
  primary: '#8aebff'
  on-primary: '#00363e'
  primary-container: '#22d3ee'
  on-primary-container: '#005763'
  inverse-primary: '#006877'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#ffd6a3'
  on-tertiary: '#462b00'
  tertiary-container: '#ffb13b'
  on-tertiary-container: '#6e4600'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#a2eeff'
  primary-fixed-dim: '#2fd9f4'
  on-primary-fixed: '#001f25'
  on-primary-fixed-variant: '#004e5a'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#ffddb5'
  tertiary-fixed-dim: '#ffb957'
  on-tertiary-fixed: '#2a1800'
  on-tertiary-fixed-variant: '#643f00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin: 32px
  container-padding: 20px
---

## Brand & Style
The design system is engineered for high-fidelity quantum computing interfaces. The brand personality is scientific, precise, and forward-looking, evoking the atmosphere of a deep-space laboratory or a high-end IDE. 

The aesthetic leverages **Glassmorphism** and **High-Tech Minimalism**. Interfaces should feel like "light projected onto dark glass." Use semi-transparent layers, subtle glowing borders, and sharp, monospaced data points to emphasize the complexity and precision of quantum state monitoring. The emotional response should be one of sophisticated control and focused clarity.

## Colors
The palette is rooted in a deep-space spectrum.
- **Base Surfaces:** Use `#0f172a` (Slate 950) for the application backdrop. 
- **Containers:** Use `#1e1b4b` (Dark Indigo) with varying opacities for frosted glass effects.
- **Accents:** 
    - **Cyan (#22d3ee):** Used for primary actions, active quantum states, and stable metrics.
    - **Violet (#8b5cf6):** Used for secondary logic, probabilistic data, and complex algorithmic paths.
- **Functional:** Success states use Cyan; Warning states use a desaturated Amber; Error states use a high-vibrancy Pink/Red to contrast against the cold blue background.

## Typography
This design system employs a dual-font strategy:
- **Inter** handles all UI scaffolding, navigation, and instructional text. It provides a clean, human-readable foundation that balances the technical nature of the content.
- **JetBrains Mono** is reserved for all variable data, quantum coordinates, code snippets, and telemetry. This separation ensures that the user's eye can immediately distinguish between "interface" and "computation."

All labels (`label-caps`) should be set in uppercase to reinforce the scientific instrumentation aesthetic. Use `data-lg` for large-scale metric monitoring.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a strictly enforced 4px base unit. 
- **Structure:** Use a 12-column grid for desktop views. Containers should utilize `backdrop-filter: blur(12px)` to maintain legibility over complex background gradients.
- **Rhythm:** Dense data displays should use 8px (2 units) of internal padding, while editorial or high-level dashboard views should use 24px (6 units) to allow for "visual breathing room."
- **Breakpoints:** 
  - Mobile (<768px): 4 columns, 16px margins.
  - Tablet (768px - 1280px): 8 columns, 24px margins.
  - Desktop (>1280px): 12 columns, 32px margins.

## Elevation & Depth
Depth is created through **Luminance and Translucency** rather than traditional drop shadows.
- **Level 0 (Floor):** Deep Slate (#0f172a).
- **Level 1 (Panels):** Dark Indigo (#1e1b4b) at 40% opacity with a 1px solid border at 10% white opacity.
- **Level 2 (Popovers/Modals):** Dark Indigo at 80% opacity with a subtle Cyan outer glow (`box-shadow: 0 0 15px rgba(34, 211, 238, 0.1)`).
- **Interactions:** When an element is hovered, the border opacity should increase from 10% to 40% white, and the backdrop blur should intensify.

## Shapes
The shape language is **Soft (0.25rem)**. This provides a precision-engineered look that avoids the aggressive sharpness of brutalism while remaining more professional and "industrial" than fully rounded consumer apps. 

Use sharp 0px corners only for data-grid cells and code blocks. All glass containers and primary buttons must use the `rounded-md` (0.25rem) or `rounded-lg` (0.5rem) standard to maintain a modern, refined silhouette.

## Components
- **Buttons:** Primary buttons use a solid Cyan fill with black text. Secondary buttons use a transparent background with a 1px Cyan border and Cyan text. Use a subtle "glow" transition on hover.
- **Cards/Containers:** Must feature `backdrop-filter: blur(16px)` and a top-down linear gradient border (White 20% to White 5%) to simulate light hitting the edge of a glass pane.
- **Input Fields:** Darker than the container background. Use JetBrains Mono for the input text. On focus, the border should glow with the Primary Cyan.
- **Status Chips:** Small, monospaced text with a leading "dot" icon. Stable states = Cyan; Fluctuating = Violet; Critical = Pink.
- **Data Visualizations:** Use thin strokes (1px or 1.5px). Avoid solid area fills; use gradients that bleed into transparency to maintain the "light-based" aesthetic.
- **Telemetry Lists:** Use alternating row highlights at 5% white opacity. Ensure all numerical columns are right-aligned using JetBrains Mono for tabular lining.

## Google Stitch prototype: ./Frontend-prototype

Frontend Design:

Context: Design a web-based dashboard for Q-Weave, a quantum compiler framework that mitigates crosstalk in quantum circuits.User: Computer science evaluation panels analyzing compiler optimization metrics.Goal of the screen: Visualize the mitigation pipeline from noise characterization to circuit transformation and final fidelity metrics.Screen type: Web App Dashboard (Desktop-optimized).Structural RequirementsHeader & Sidebar: A top navigation bar with the title "Q-Weave Engine". A left sidebar containing a dropdown for benchmark circuits like GHZ, QAOA, and QFT, alongside a slider for synthetic noise and a "Run Mitigation" button.  Main Area - Tab 1 (Hardware Model): A network graph component displaying qubits and crosstalk severity edges, paired with a small interaction matrix table.  Main Area - Tab 2 (Compiler Pass): Two side-by-side panels comparing the standard Qiskit compilation against the Q-Weave mitigated schedule.  Main Area - Tab 3 (Evaluation): Metric summary cards for execution fidelity, circuit depth, and two-qubit gate count, sitting above a multi-bar chart comparing execution success probabilities.  Visual Direction & ConstraintsTheme: Deep dark mode using slate and dark indigo backgrounds to establish a high-tech quantum aesthetic.Styling: Use glowing neon accents (cyan and violet) for data visualizations, active network paths, and primary UI elements.Typography & Surfaces: Apply frosted glassmorphism for component containers and use monospaced fonts for numerical data and code blocks.Scope Constraints: Exclude any interfaces for real-time hardware manipulation, microwave pulse generators, or chat prompts. The focus must remain entirely on software-level compiler transformations.

## Updated sections
1. Update Section 8: Qiskit Aer and the crosstalk simulationWhere: Replace the existing paragraph about hidden rules in Section 8.  What to update:Explain that NoiseModel.add_nonlocal_quantum_error() was removed in Aer 0.12+.  Mandate explicit noise gate injection using DAG topological layers and standard add_quantum_error().  Pin dependencies: qiskit>=1.0 and qiskit-aer>=0.14.  Add the fixed noise tier table and the guaranteed injection function:  LabelExtra Depolarizing ProbHIGH0.15MEDIUM0.07LOW0.02

import itertools
from qiskit.circuit import Instruction
from qiskit.converters import circuit_to_dag
from qiskit_aer.noise import NoiseModel, depolarizing_error


def inject_crosstalk(qc, hidden_rules):
  """hidden_rules: dict[frozenset[tuple(qubits_A), tuple(qubits_B)]] -> extra_error_prob

  Only the environment-builder ever sees this dict. Q-Weave's profiler never
  does.
  """
  dag = circuit_to_dag(qc)
  new_qc = qc.copy_empty_like()
  injected_names = {}  # gate_name -> (qubits, prob)

  for layer in dag.layers():
    nodes = list(layer["graph"].op_nodes())
    for node in nodes:
      new_qc.append(node.op, node.qargs, node.cargs)
    for a, b in itertools.combinations(nodes, 2):
      qa = tuple(q._index for q in a.qargs)
      qb = tuple(q._index for q in b.qargs)
      key = frozenset([qa, qb])
      if key in hidden_rules:
        combined = tuple(sorted(set(qa) | set(qb)))
        name = f"xtalk_{'_'.join(map(str, combined))}_{a.name}_{b.name}"
        injected_names[name] = (combined, hidden_rules[key])
        new_qc.append(Instruction(name, len(combined), 0, []), combined)

  noise_model = NoiseModel()
  for name, (qubits, prob) in injected_names.items():
    err = depolarizing_error(prob, len(qubits))
    noise_model.add_quantum_error(err, name, qubits)

  return new_qc, noise_model
2. Update Section 10: Interaction estimationWhere: Replace the placeholder text in Section 10.  What to update: Add the exact statistical estimator and significance gate:  $$F_{\text{expect}} = F_A \times F_B$$$$\text{raw} = \max(0, F_{\text{expect}} - F_{AB})$$$$\text{SE} = \sqrt{\frac{F(1-F)}{\text{shots}}} \quad \text{for } F_A, F_B, F_{AB}$$$$\text{interaction}(A,B) = \begin{cases} \frac{\text{raw}}{F_{\text{expect}}} & \text{if } \text{raw} > 3 \sqrt{\text{SE}_A^2 + \text{SE}_B^2 + \text{SE}_{AB}^2} \\ 0 & \text{otherwise} \end{cases}$$Execution parameters: Set shot count to 8,192 per probe circuit with 5 random seed repeats, reporting the mean and standard error.  3. Update Section 13: Mitigation mechanism 1 — Crosstalk-aware placementWhere: Replace the note under "Important" in Section 13.  What to update: Specify the 2-opt local search placement algorithm:  Initialize with Qiskit’s default SabreLayout mapping.  Compute total interaction weight $\sum W(\text{interaction\_graph edges})$ for adjacent mapped qubits.  Swap physical assignments iteratively, keeping swaps that reduce the sum.  Stop when no swap improves the cost or after 200 iterations.  4. Update Section 15: Scheduling algorithm for the MVPWhere: Replace the conceptual cost function formula in Section 15.  What to update: Insert the normalized cost function:  $$\text{cost} = 1.0 \cdot \text{depth\_term} + 0.5 \cdot \text{gate\_term} + 2.0 \cdot \text{error\_term} + 5.0 \cdot \text{crosstalk\_term}$$Where:$\text{depth\_term} = \frac{\text{new\_depth} - \text{current\_depth}}{1}$  $\text{gate\_term} = \frac{1}{\text{total\_remaining\_two\_qubit\_gates}}$  $\text{error\_term} = \text{estimated\_gate\_error}$  $\text{crosstalk\_term} = \frac{\sum \text{interaction\_weight}}{\text{max\_observed\_interaction}}$  5. Update Section 20: Evaluation metricsWhere: Under "Hellinger fidelity" in Section 20.  What to update: Include the standalone, version-safe Hellinger fidelity implementation:  

2. Update Section 10: Interaction estimationWhere: Replace the placeholder text in Section 10.  What to update: Add the exact statistical estimator and significance gate:  $$F_{\text{expect}} = F_A \times F_B$$$$\text{raw} = \max(0, F_{\text{expect}} - F_{AB})$$$$\text{SE} = \sqrt{\frac{F(1-F)}{\text{shots}}} \quad \text{for } F_A, F_B, F_{AB}$$$$\text{interaction}(A,B) = \begin{cases} \frac{\text{raw}}{F_{\text{expect}}} & \text{if } \text{raw} > 3 \sqrt{\text{SE}_A^2 + \text{SE}_B^2 + \text{SE}_{AB}^2} \\ 0 & \text{otherwise} \end{cases}$$Execution parameters: Set shot count to 8,192 per probe circuit with 5 random seed repeats, reporting the mean and standard error.  3. Update Section 13: Mitigation mechanism 1 — Crosstalk-aware placementWhere: Replace the note under "Important" in Section 13.  What to update: Specify the 2-opt local search placement algorithm:  Initialize with Qiskit’s default SabreLayout mapping.  Compute total interaction weight $\sum W(\text{interaction\_graph edges})$ for adjacent mapped qubits.  Swap physical assignments iteratively, keeping swaps that reduce the sum.  Stop when no swap improves the cost or after 200 iterations.  4. Update Section 15: Scheduling algorithm for the MVPWhere: Replace the conceptual cost function formula in Section 15.  What to update: Insert the normalized cost function:  $$\text{cost} = 1.0 \cdot \text{depth\_term} + 0.5 \cdot \text{gate\_term} + 2.0 \cdot \text{error\_term} + 5.0 \cdot \text{crosstalk\_term}$$Where:$\text{depth\_term} = \frac{\text{new\_depth} - \text{current\_depth}}{1}$  $\text{gate\_term} = \frac{1}{\text{total\_remaining\_two\_qubit\_gates}}$  $\text{error\_term} = \text{estimated\_gate\_error}$  $\text{crosstalk\_term} = \frac{\sum \text{interaction\_weight}}{\text{max\_observed\_interaction}}$  5. Update Section 20: Evaluation metricsWhere: Under "Hellinger fidelity" in Section 20.  What to update: Include the standalone, version-safe Hellinger fidelity implementation:  

6. Update Section 21 & 22: Success Criteria & DefinitionsWhere: Append to Section 21 and Section 22.  What to update:Level 2 Success Threshold: Mitigated fidelity must exceed standard compilation fidelity by more than $2 \times$ the combined standard error in at least 2 out of 3 noise tiers.  Synthetic Topology: Mandate a fixed coupling topology (e.g., a fixed $3 \times 3$ grid or standard small fake backend) across all runs to ensure comparability.  Layer Definition: Explicitly define "Layer" as Qiskit DAG topological layers: circuit_to_dag(qc).layers().  7. Update Section 42: Web UI and API ArchitectureWhere: At the start of Section 42.  What to update: Add a warning header declaring Section 42 a non-critical presentation layer that must be built only after the compiler backend passes all Level 1 and Level 2 evaluations.  

