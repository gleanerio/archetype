#!/usr/bin/env python3
"""Launch the local ODIS Search Explorer UI."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from odis_explorer.__main__ import main

if __name__ == "__main__":
    main()
