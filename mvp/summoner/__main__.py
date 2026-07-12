"""CLI entry: python -m summoner --config mvp_config.yaml"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .config import load_config
from .crawl import run_crawl


def _default_config_path() -> Path:
    # Prefer mvp_config.yaml next to the package's parent (mvp/)
    mvp_dir = Path(__file__).resolve().parent.parent
    candidate = mvp_dir / "mvp_config.yaml"
    if candidate.is_file():
        return candidate
    return Path("mvp_config.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="summoner",
        description=(
            "MVP sitemap → JSON-LD → S3 summoner. "
            "Static by default; sources with headless:true use Browserless when configured."
        ),
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="Path to mvp_config.yaml (default: mvp/mvp_config.yaml or ./mvp_config.yaml)",
    )
    parser.add_argument(
        "--source",
        "-s",
        default=None,
        help="Only process this source name (must be active)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max page URLs per source (for smoke tests)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract JSON-LD but do not write to object store",
    )
    parser.add_argument(
        "--rude",
        action="store_true",
        help="Ignore robots.txt (use sparingly)",
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
    # Quieter HTTP internals unless verbose
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
        result = run_crawl(
            cfg,
            source_name=args.source,
            limit=args.limit,
            dry_run=args.dry_run,
            rude=args.rude,
        )
    except ValueError as exc:
        logging.error("%s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        logging.error("Crawl failed: %s", exc)
        return 1

    print("--- summary ---")
    total_stored = 0
    total_errors = 0
    for stats in result.sources:
        print(stats.summary())
        total_stored += stats.stored
        total_errors += stats.errors

    if not result.sources:
        return 2
    # Soft success: completed walk even if some pages failed
    if total_stored == 0 and total_errors > 0 and not args.dry_run:
        # Still exit 0 if we only had extraction misses; store misconfig already raised
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
