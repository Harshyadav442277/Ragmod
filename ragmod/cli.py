"""CLI entrypoint. Wave 0: gateway smoke helpers. Wave 1+: ask / bench."""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv


def main(argv: list[str] | None = None) -> int:
    from ragmod.gateway.proxy import repo_root

    load_dotenv(repo_root() / ".env")
    parser = argparse.ArgumentParser(prog="ragmod", description="Ragmod CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_stats = sub.add_parser("stats", help="Print Paritok /stats as SavingsStats")
    p_stats.add_argument("--port", type=int, default=None)

    p_health = sub.add_parser("health", help="Check Paritok proxy /health")
    p_health.add_argument("--port", type=int, default=None)

    p_ask = sub.add_parser("ask", help="Ask a question about a checked-out repository")
    p_ask.add_argument("question")
    p_ask.add_argument("--repo", default=".", help="Repository to inspect (default: current directory)")
    p_ask.add_argument("--port", type=int, default=None, help="Paritok proxy port")
    p_ask.add_argument("--model", default=None, help="Upstream model name")
    p_ask.add_argument("--max-turns", type=int, default=8)

    args = parser.parse_args(argv)

    from ragmod.gateway import (
        fetch_stats,
        proxy_base_url,
        proxy_health,
        stats_to_savings,
    )

    base = proxy_base_url(args.port)

    if args.cmd == "ask":
        from ragmod.agent import ProxyChatClient, ask

        answer = ask(
            args.question,
            args.repo,
            client=ProxyChatClient(base_url=base),
            model=args.model,
            max_turns=args.max_turns,
        )
        print(answer["text"])
        if answer["citations"]:
            print("\nSources:")
            for citation in answer["citations"]:
                print(f"- {citation['path']}:{citation['start']}-{citation['end']}")
        print(f"\nTurns: {answer['turns']}")
        return 0

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
