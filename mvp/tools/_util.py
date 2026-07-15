"""Shared helpers for tool adapters."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Resolve mvp_config.yaml: explicit path, else mvp/mvp_config.yaml beside tools/."""
    if config_path is not None:
        path = Path(config_path)
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        return path

    mvp_dir = Path(__file__).resolve().parent.parent
    candidate = mvp_dir / "mvp_config.yaml"
    if candidate.is_file():
        return candidate
    cwd = Path("mvp_config.yaml")
    if cwd.is_file():
        return cwd
    raise FileNotFoundError(
        "No config_path given and mvp_config.yaml not found next to tools/ or in cwd"
    )


def stats_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a dataclass stats object (or similar) to a plain dict."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    raise TypeError(f"Cannot convert {type(obj)!r} to dict")


def ok_result(**payload: Any) -> dict[str, Any]:
    return {"ok": True, **payload}


def err_result(error: str, **payload: Any) -> dict[str, Any]:
    return {"ok": False, "error": error, **payload}
