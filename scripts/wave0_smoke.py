#!/usr/bin/env python3
"""Wave 0 gate: one real LLM call through Paritok hosted GPU with fat tool_result.

Done when /stats shows non-zero tokens_saved.

Usage (two terminals):
  # terminal 1
  export PARITOK_API_KEY=pk_live_...
  paritok proxy --port 8080 --config-file paritok.yaml

  # terminal 2
  export PARITOK_API_KEY=pk_live_...
  export OPENAI_API_KEY=sk-...   # or ANTHROPIC_API_KEY
  python scripts/wave0_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from ragmod.gateway import (  # noqa: E402
    ensure_paritok_yaml,
    fetch_stats,
    proxy_base_url,
    resolve_paritok_api_key,
    stats_to_savings,
    wait_for_proxy,
)
from ragmod.tools.base import openai_tool_schemas  # noqa: E402


def fat_tool_result() -> str:
    """On-distribution code blob — Paritok compresses tool_result / file_read shape."""
    sample = (ROOT / "ragmod" / "gateway" / "proxy.py").read_text(encoding="utf-8")
    # Keep under Groq free-tier TPM (~6k) while still giving Paritok a fat tool_result.
    body = "\n\n".join(
        f"# --- read_file ragmod/gateway/proxy.py pass {i} ---\n{sample}" for i in range(2)
    )
    return body


def build_openai_payload(model: str) -> dict:
    tool_call_id = "call_wave0_read_file"
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a terse code assistant. Answer from the tool result only. "
                    "One short sentence."
                ),
            },
            {
                "role": "user",
                "content": "What does ensure_paritok_yaml do?",
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps(
                                {"path": "ragmod/gateway/proxy.py"}
                            ),
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": fat_tool_result(),
            },
        ],
        "tools": openai_tool_schemas(),
        "max_tokens": 80,
    }


def main() -> int:
    ensure_paritok_yaml()

    if not resolve_paritok_api_key():
        print(
            "Missing PARITOK_API_KEY (env or paritok.yaml gpu_server.api_key).\n"
            "Get one at https://paritok.com → dashboard → API keys.",
            file=sys.stderr,
        )
        return 2

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not openai_key:
        print(
            "Missing OPENAI_API_KEY (upstream LLM; proxy forwards it).\n"
            "Free option — Groq (no card):\n"
            "  1. https://console.groq.com/keys\n"
            "  2. Put in .env:\n"
            "       OPENAI_API_KEY=gsk_...\n"
            "       RAGMOD_OPENAI_URL=https://api.groq.com/openai\n"
            "       RAGMOD_MODEL=llama-3.1-8b-instant\n"
            "  3. Restart ./scripts/start_proxy.sh then re-run this script.",
            file=sys.stderr,
        )
        return 2

    base = proxy_base_url()
    print(f"Waiting for proxy at {base} ...")
    try:
        health = wait_for_proxy(base, timeout_s=30)
    except TimeoutError as e:
        print(str(e), file=sys.stderr)
        print(
            "Start it with:\n"
            "  paritok proxy --port 8080 --config-file paritok.yaml",
            file=sys.stderr,
        )
        return 1
    print("health:", json.dumps(health))

    before = stats_to_savings(fetch_stats(base))
    print("stats before:", json.dumps(before, indent=2))

    model = os.environ.get("RAGMOD_MODEL", "gpt-4o-mini")
    payload = build_openai_payload(model)
    url = f"{base}/v1/chat/completions"
    print(f"POST {url} model={model} (fat tool_result) ...")

    with httpx.Client(timeout=180.0) as client:
        resp = client.post(
            url,
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if resp.status_code >= 400:
        print(f"upstream/proxy error {resp.status_code}:\n{resp.text}", file=sys.stderr)
        return 1

    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        text = json.dumps(data)[:500]
    print("model reply:", text)

    after_raw = fetch_stats(base)
    after = stats_to_savings(after_raw)
    print("stats after:", json.dumps(after, indent=2))
    print("raw /stats:", json.dumps(after_raw, indent=2))

    if after["saved"] <= 0:
        print(
            "FAIL: tokens_saved is still 0. Compression did not engage "
            "(check tool_result shape / use_gpu_server).",
            file=sys.stderr,
        )
        return 1

    print(
        f"\nWAVE 0 PASS — tokens_saved={after['saved']} "
        f"ratio={after['ratio']} cost_saved={after['cost_saved_usd']}"
    )
    print("Confirm the same call on the Paritok dashboard at https://paritok.com")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
