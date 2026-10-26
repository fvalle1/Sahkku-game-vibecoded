"""``python -m sahkku`` starts the app and opens the browser."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m sahkku",
        description="Unofficial, rules-configurable version of the Sámi board game sáhkku.",
    )
    ap.add_argument("--port", type=int, default=8080, help="port to serve on (default 8080)")
    ap.add_argument(
        "--host",
        default="127.0.0.1",
        help="address to bind; use 0.0.0.0 to reach it from phones on your local network only",
    )
    ap.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    ap.add_argument("--seed", type=int, default=None, help="seed for the first game (replays)")
    ap.add_argument(
        "--ai-delay", type=float, default=0.6, help="seconds the computer waits before each move"
    )
    args = ap.parse_args(argv)

    from .ui.app import run

    run(
        host=args.host,
        port=args.port,
        show=not args.no_browser,
        seed=args.seed,
        ai_delay=args.ai_delay,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
