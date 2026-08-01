"""CLI entrypoint. Wave 0: gateway smoke helpers. Wave 1+: ask / bench."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ragmod", description="Ragmod CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_stats = sub.add_parser("stats", help="Print Paritok /stats as SavingsStats")
    p_stats.add_argument("--port", type=int, default=None)

    p_health = sub.add_parser("health", help="Check Paritok proxy /health")
    p_health.add_argument("--port", type=int, default=None)

    args = parser.parse_args(argv)

    from ragmod.gateway import (
        fetch_stats,
        proxy_base_url,
        proxy_health,
        stats_to_savings,
    )

    base = proxy_base_url(args.port)

    if args.cmd == "health":
        health = proxy_health(base)
        if health is None:
            print(f"unhealthy: {base}", file=sys.stderr)
            return 1
        print(json.dumps(health, indent=2))
        return 0

    if args.cmd == "stats":
        raw = fetch_stats(base)
        print(json.dumps(stats_to_savings(raw), indent=2))
        print("--- raw ---")
        print(json.dumps(raw, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
