"""CLI for multi-agent supervisor (OpenRouter / Grok 4.5).

Examples:
  export OPENROUTER_API_KEY=sk-or-...
  python -m agents "dry-run the medin pipeline with limit 3"
  python -m agents --agent diagnoser "why might oxigraph be empty for medin?"
  python -m agents --show-config
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from agents.builders import build_specialist, build_supervisor_agent, invoke_agent, last_message_text
from agents.defaults import set_defaults
from agents.llm import LLMConfigError, describe_llm_config, get_default_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agents",
        description="MVP multi-agent supervisor via OpenRouter (default model: x-ai/grok-4.5).",
    )
    parser.add_argument(
        "goal",
        nargs="?",
        default=None,
        help="Natural-language goal for the agent",
    )
    parser.add_argument(
        "--agent",
        "-a",
        choices=("supervisor", "summoner", "scribe", "indexer", "diagnoser"),
        default="supervisor",
        help="Which agent to run (default: supervisor with handoffs)",
    )
    parser.add_argument("--config", "-c", default=None, help="mvp_config.yaml path")
    parser.add_argument("--source", "-s", default="medin")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Default true; --no-dry-run allows real writes via tools",
    )
    parser.add_argument("--rude", action="store_true")
    parser.add_argument("--model", default=None, help=f"OpenRouter model id (default {get_default_model()})")
    parser.add_argument("--recursion-limit", type=int, default=40)
    parser.add_argument("--show-config", action="store_true", help="Print LLM config and exit")
    parser.add_argument("--json", action="store_true", help="Print full result JSON")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quieter HTTP unless verbose
    if not args.verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)

    if args.show_config:
        print(json.dumps(describe_llm_config(require_key=False), indent=2))
        return 0

    if not args.goal:
        parser.error("goal is required unless --show-config")

    set_defaults(
        config_path=args.config,
        source=args.source,
        limit=args.limit,
        dry_run=args.dry_run,
        rude=args.rude,
    )

    try:
        from agents.llm import get_chat_model

        model = get_chat_model(model=args.model) if args.model else get_chat_model()
        if args.agent == "supervisor":
            agent = build_supervisor_agent(model=model)
        else:
            agent = build_specialist(args.agent, model=model)  # type: ignore[arg-type]
        raw = invoke_agent(agent, args.goal, recursion_limit=args.recursion_limit)
    except LLMConfigError as exc:
        logging.error("%s", exc)
        return 2
    except ImportError as exc:
        logging.error("%s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        logging.error("Agent failed: %s", exc)
        if args.verbose:
            raise
        return 1

    reply = last_message_text(raw)
    if args.json:
        # messages may not be fully JSON serializable
        out = {
            "agent": args.agent,
            "goal": args.goal,
            "reply": reply,
            "llm": describe_llm_config(require_key=False),
        }
        print(json.dumps(out, indent=2, default=str))
    else:
        print(reply)

    return 0


if __name__ == "__main__":
    sys.exit(main())
