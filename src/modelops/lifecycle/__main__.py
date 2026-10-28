"""CLI: ``python -m modelops.lifecycle promote|rollback|compare``."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from modelops.config import load_config
from modelops.lifecycle.promote import PromotionError, promote_candidate, rollback_approved


def _cmd_promote(args: argparse.Namespace) -> int:
    config = load_config()
    try:
        result = promote_candidate(
            candidate_model=args.model,
            candidate_metrics=args.metrics,
            config=config,
            require_improvement=args.require_improvement,
            force=args.force,
        )
    except PromotionError as exc:
        logging.error("%s", exc)
        return 1

    print(json.dumps(result.as_dict(), indent=2))
    if not result.promoted:
        logging.error("Promotion blocked: %s", "; ".join(result.gate.failures))
        return 2
    return 0


def _cmd_rollback(_args: argparse.Namespace) -> int:
    config = load_config()
    try:
        payload = rollback_approved(config=config)
    except PromotionError as exc:
        logging.error("%s", exc)
        return 1
    print(json.dumps(payload, indent=2))
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    config = load_config()
    from modelops.tracking.mlflow_run import list_recent_runs

    rows = list_recent_runs(config, max_results=args.limit)
    print(json.dumps(rows, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ModelOps lifecycle commands")
    sub = parser.add_subparsers(dest="command", required=True)

    promote_p = sub.add_parser("promote", help="Promote gated candidate to approved")
    promote_p.add_argument("--model", type=Path, default=None)
    promote_p.add_argument("--metrics", type=Path, default=None)
    promote_p.add_argument(
        "--require-improvement",
        action="store_true",
        help="Require MAE <= current approved MAE when an approved model exists",
    )
    promote_p.add_argument(
        "--force",
        action="store_true",
        help="Promote even if quality gates fail (escape hatch; logged)",
    )
    promote_p.set_defaults(func=_cmd_promote)

    rollback_p = sub.add_parser("rollback", help="Restore previous approved snapshot")
    rollback_p.set_defaults(func=_cmd_rollback)

    compare_p = sub.add_parser("compare", help="List recent MLflow runs")
    compare_p.add_argument("--limit", type=int, default=10)
    compare_p.set_defaults(func=_cmd_compare)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
