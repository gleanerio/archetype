"""CLI: python -m scribe --config mvp_config.yaml --source medin"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .config import load_config
from .load import run_load


def _default_config_path() -> Path:
    mvp_dir = Path(__file__).resolve().parent.parent
    candidate = mvp_dir / "mvp_config.yaml"
    if candidate.is_file():
        return candidate
    return Path("mvp_config.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scribe",
        description="MVP load summoned JSON-LD from S3 into Oxigraph as named-graph quads.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="Path to mvp_config.yaml",
    )
    parser.add_argument(
        "--source",
        "-s",
        required=True,
        help="Source name (S3 prefix summoned/<name>/), e.g. medin",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max objects to load (smoke tests)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Convert only; do not CLEAR or POST to Oxigraph",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    if not args.verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    config_path = args.config or _default_config_path()
    try:
        cfg = load_config(config_path)
    except (OSError, ValueError) as exc:
        logging.error("Failed to load config %s: %s", config_path, exc)
        return 2

    try:
        stats = run_load(
            cfg,
            args.source,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    except Exception as exc:  # noqa: BLE001
        logging.error("Load failed: %s", exc)
        return 1

    print("--- summary ---")
    print(stats.summary())

    if stats.objects_seen == 0:
        return 2
    if not stats.dry_run and not stats.loaded:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
