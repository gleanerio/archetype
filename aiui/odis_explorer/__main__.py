"""Run the local ODIS explorer: python -m odis_explorer [--port 8765] [--open]."""

from __future__ import annotations

import argparse
import webbrowser

import uvicorn

from odis_explorer.client import DEFAULT_BASE_URL
from odis_explorer.server import app, configure_client


def main() -> None:
    parser = argparse.ArgumentParser(description="ODIS Search Explorer (local web UI)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    parser.add_argument("--open", action="store_true", help="Open the UI in a browser")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"ODIS Search API origin (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--backend",
        default="elasticsearch",
        help="X-Search-Backend value (default: elasticsearch)",
    )
    args = parser.parse_args()

    configure_client(base_url=args.base_url, backend=args.backend)
    url = f"http://{args.host}:{args.port}/"
    print(f"ODIS Search Explorer at {url}")
    if args.open:
        webbrowser.open(url)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
