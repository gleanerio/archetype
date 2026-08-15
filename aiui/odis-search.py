#!/usr/bin/env python3
"""
Query the ODIS search-demo API.

Usage:
    python odis-search.py "coral"
    python odis-search.py "coral" --page 2 --size 10
    python odis-search.py "coral" --source ocean-biodiversity-information-system
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python odis-search.py` from this directory without installing a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from odis_explorer.client import DEFAULT_BASE_URL, MAX_PAGE_SIZE, OdisSearchClient, OdisSearchError


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the ODIS search-demo API")
    parser.add_argument("query", nargs="?", default="", help="Search query string")
    parser.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    parser.add_argument(
        "--size",
        type=int,
        default=20,
        help=f"Results per page, 1-{MAX_PAGE_SIZE} (default: 20)",
    )
    parser.add_argument(
        "--type",
        dest="types",
        action="append",
        default=None,
        help="Type filter, repeatable (default: Dataset)",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=None,
        help="Source filter, repeatable (default: no source filter)",
    )
    parser.add_argument(
        "--sort",
        choices=("relevance", "title"),
        default="relevance",
        help="Sort order (default: relevance)",
    )
    parser.add_argument(
        "--include-graph-fragments",
        action="store_true",
        help="Include JSON-LD graph fragment node types in the hit list",
    )
    parser.add_argument(
        "--record",
        metavar="ID",
        help="Fetch one record by id (with raw JSON-LD) instead of searching",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API origin")
    args = parser.parse_args()

    client = OdisSearchClient(base_url=args.base_url)
    try:
        if args.record:
            payload = client.get_record(args.record, raw=True)
            if payload is None:
                print(f"Record not found: {args.record}", file=sys.stderr)
                return 1
        else:
            types = args.types if args.types is not None else ["Dataset"]
            payload = client.search(
                args.query,
                types=types,
                sources=args.source,
                sort=args.sort,
                page=args.page,
                size=args.size,
                include_graph_fragments=args.include_graph_fragments,
            )
    except (OdisSearchError, ValueError) as exc:
        print(exc, file=sys.stderr)
        if isinstance(exc, OdisSearchError) and exc.body:
            print(exc.body, file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
