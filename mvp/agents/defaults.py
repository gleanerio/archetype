"""Runtime defaults shared by tool bindings (config path, dry_run, limit)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _default_config_path() -> str:
    mvp_dir = Path(__file__).resolve().parent.parent
    candidate = mvp_dir / "mvp_config.yaml"
    if candidate.is_file():
        return str(candidate)
    return "mvp_config.yaml"


@dataclass
class AgentDefaults:
    """Safe defaults injected into LangChain tools."""

    config_path: str = field(default_factory=_default_config_path)
    source: str = "medin"
    limit: int | None = 5
    dry_run: bool = True
    rude: bool = False


# Process-wide defaults; CLI / supervisor can replace via set_defaults()
_CURRENT = AgentDefaults()


def get_defaults() -> AgentDefaults:
    return _CURRENT


def set_defaults(
    *,
    config_path: str | None = None,
    source: str | None = None,
    limit: int | None | object = ...,
    dry_run: bool | None = None,
    rude: bool | None = None,
) -> AgentDefaults:
    global _CURRENT
    cur = _CURRENT
    _CURRENT = AgentDefaults(
        config_path=config_path if config_path is not None else cur.config_path,
        source=source if source is not None else cur.source,
        limit=cur.limit if limit is ... else limit,  # type: ignore[arg-type]
        dry_run=cur.dry_run if dry_run is None else dry_run,
        rude=cur.rude if rude is None else rude,
    )
    return _CURRENT
