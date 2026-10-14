"""
Q-Weave: A Crosstalk-Aware Error Mitigation Framework for NISQ Circuits.

Core thesis: MEASURE -> MODEL -> MITIGATE -> EXECUTE -> EVALUATE
"""

__version__ = "0.1.0"
__author__ = "Q-Weave Team"

# Lazy imports - components will be available after Phase 1 implementation
__all__ = [
    "CrosstalkProfiler",
    "CrosstalkGraph",
    "MitigationEngine",
]


def __getattr__(name):
    """Lazy import for main components."""
    if name == "CrosstalkProfiler":
        from qweave.characterization.profiler import CrosstalkProfiler
        return CrosstalkProfiler
    elif name == "CrosstalkGraph":
        from qweave.crosstalk_model.graph import CrosstalkGraph
        return CrosstalkGraph
    elif name == "MitigationEngine":
        from qweave.mitigation.engine import MitigationEngine
        return MitigationEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")