"""CLI: python -m graph --source medin --limit 3 --dry-run"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .pipeline import run_langgraph_pipeline, run_pipeline
from .state import initial_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graph",
        description="Run MVP linear pipeline (preflight → summon → scribe∥indexer → verify).",
    )
    parser.add_argument("--config", "-c", default=None, help="Path to mvp_config.yaml")
    parser.add_argument("--source", "-s", default="medin")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Default true; use --no-dry-run for real writes",
    )
    parser.add_argument("--rude", action="store_true")
    parser.add_argument("--skip-summon", action="store_true")
    parser.add_argument("--skip-scribe", action="store_true")
    parser.add_argument("--skip-indexer", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument(
        "--langgraph",
        action="store_true",
        help="Use LangGraph compiled graph (requires requirements-agents.txt)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full state as JSON",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    state = initial_state(
        source=args.source,
        config_path=args.config,
        limit=args.limit,
        dry_run=args.dry_run,
        rude=args.rude,
        skip_summon=args.skip_summon,
        skip_scribe=args.skip_scribe,
        skip_indexer=args.skip_indexer,
        skip_verify=args.skip_verify,
    )

    try:
        if args.langgraph:
            result = run_langgraph_pipeline(state)
        else:
            result = run_pipeline(state)
    except ImportError as exc:
        logging.error("%s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        logging.error("Pipeline failed: %s", exc)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("--- pipeline summary ---")
        print(f"source={result.get('source')} dry_run={result.get('dry_run')} limit={result.get('limit')}")
        print(f"stages={result.get('stages_done')}")
        if result.get("summon_stats"):
            print("summon:", result["summon_stats"].get("summary") or result["summon_stats"].get("error"))
        if result.get("scribe_stats"):
            print("scribe:", result["scribe_stats"].get("summary") or result["scribe_stats"].get("error"))
        if result.get("indexer_stats"):
            print(
                "indexer:",
                result["indexer_stats"].get("summary") or result["indexer_stats"].get("error"),
            )
        if result.get("verify_graph_result"):
            vg = result["verify_graph_result"]
            print("verify graph:", vg.get("data"), vg.get("prov") if isinstance(vg, dict) else vg)
        if result.get("verify_index_result"):
            print("verify index:", result["verify_index_result"])
        if result.get("errors"):
            print("errors:")
            for e in result["errors"]:
                print(f"  - {e}")

    return 1 if result.get("errors") and not result.get("dry_run") else 0


if __name__ == "__main__":
    sys.exit(main())
