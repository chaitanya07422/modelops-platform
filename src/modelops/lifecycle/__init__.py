"""Model lifecycle: quality gates, promotion, and rollback."""

from __future__ import annotations

from typing import Any

__all__ = [
    "GateResult",
    "PromoteResult",
    "evaluate_quality_gates",
    "promote_candidate",
    "rollback_approved",
]


def __getattr__(name: str) -> Any:
    # Lazy exports avoid circular imports with modelops.training.
    if name in {"GateResult", "evaluate_quality_gates"}:
        from modelops.lifecycle.gates import GateResult, evaluate_quality_gates

        return {
            "GateResult": GateResult,
            "evaluate_quality_gates": evaluate_quality_gates,
        }[name]
    if name in {"PromoteResult", "promote_candidate", "rollback_approved"}:
        from modelops.lifecycle.promote import (
            PromoteResult,
            promote_candidate,
            rollback_approved,
        )

        return {
            "PromoteResult": PromoteResult,
            "promote_candidate": promote_candidate,
            "rollback_approved": rollback_approved,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
