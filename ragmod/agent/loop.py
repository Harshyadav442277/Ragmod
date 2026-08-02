"""OpenAI-compatible, multi-turn tool-calling loop routed through Paritok."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Protocol

import httpx

from ragmod.contracts import AgentAnswer, Citation, ToolResult
from ragmod.gateway import proxy_base_url
from ragmod.tools import RepositoryTools
from ragmod.tools.base import openai_tool_schemas

SYSTEM_PROMPT = """You are Ragmod, a codebase retrieval agent.
The conversation begins with a repository search result. Pick the file that actually
defines the behavior being asked about, then call read_file on that file before
answering. Prefer implementation modules over scripts, tests, or docs when both match.
Answer only from tool results. Never say information is unavailable when the search
result names relevant files; inspect those files instead. Be concise, explain
uncertainty, and stop calling tools once you can answer. Citations are attached from
tool metadata — reading the right file matters."""

_SEARCH_STOPWORDS = {
    "about", "available", "code", "does", "find", "from", "have", "how", "info",
    "information", "into", "please", "repository", "requested", "that", "the", "this",
    "turn", "using", "what", "where", "which", "with", "would", "you", "your",
}


class ChatClient(Protocol):
    def complete(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class ProxyChatClient:
    """OpenAI-compatible client. Default target is the local Paritok proxy."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = (base_url or proxy_base_url()).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()
        self.timeout = timeout

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the upstream model")
        # Groq free tier TPM is tight; retry briefly on 429 after Paritok compresses.
        delays = (2.0, 5.0, 15.0, 35.0)
        last_detail = ""
        with httpx.Client(timeout=self.timeout) as client:
            for attempt, delay in enumerate((*delays, None)):
                response = client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                if response.status_code != 429:
                    try:
                        response.raise_for_status()
                        return response.json()
                    except (httpx.HTTPError, ValueError) as exc:
                        detail = response.text[:500]
                        raise RuntimeError(f"Proxy request failed: {detail}") from exc
                last_detail = response.text[:500]
                if delay is None:
                    break
                time.sleep(delay)
        raise RuntimeError(f"Proxy request failed after retries: {last_detail}")


class TrackingClient:
    """Wraps a ChatClient and sums provider usage.prompt_tokens across turns."""

    def __init__(self, inner: ChatClient) -> None:
        self.inner = inner
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.requests = 0

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self.inner.complete(payload)
        usage = data.get("usage") if isinstance(data, dict) else None
        if isinstance(usage, dict):
            self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
            self.completion_tokens += int(usage.get("completion_tokens") or 0)
        self.requests += 1
        return data


def ask(
    question: str,
    repo: Path | str,
    *,
    client: ChatClient | None = None,
    tools: RepositoryTools | None = None,
    model: str | None = None,
    max_turns: int = 8,
) -> AgentAnswer:
    """Answer a repository question through a bounded tool-calling conversation."""
    if not question.strip():
        raise ValueError("question must not be empty")
    if max_turns < 1:
        raise ValueError("max_turns must be at least 1")

    tools = tools or RepositoryTools(repo)
    chat = client or ProxyChatClient()
    selected_model = model or os.environ.get("RAGMOD_MODEL", "gpt-4o-mini")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    citations: list[Citation] = []

    # Seed every run with a broad, on-distribution tool result. Small models are much
    # more reliable at selecting a file from concrete hits than inventing their first
    # ripgrep query, while Paritok still sees the retrieval as a tool_result.
    # Prefer source files for the seed search so free-tier TPM isn't spent on docs,
    # while still sending a real, compressible tool_result through Paritok.
    bootstrap_args = {"pattern": _bootstrap_search_pattern(question), "glob": "*.py"}
    bootstrap = tools.execute("search_repo", bootstrap_args)
    messages.extend(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_bootstrap_search",
                        "type": "function",
                        "function": {
                            "name": "search_repo",
                            "arguments": json.dumps(bootstrap_args),
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_bootstrap_search",
                "content": _tool_content(bootstrap),
            },
        ]
    )

    for turn in range(1, max_turns + 1):
        payload = {
            "model": selected_model,
            "messages": messages,
            "tools": openai_tool_schemas(),
            "tool_choice": "auto",
            "temperature": 0,
        }
        data = chat.complete(payload)
        message = _response_message(data)
        tool_calls = message.get("tool_calls") or []
        messages.append(_assistant_message(message))

        if not tool_calls:
            text = str(message.get("content") or "I could not produce an answer.").strip()
            return AgentAnswer(text=text, citations=_dedupe_citations(citations), turns=turn)

        for tool_call in tool_calls:
            tool_name, arguments = _tool_call_parts(tool_call)
            result = tools.execute(tool_name, arguments)
            citations.extend(result.get("meta", {}).get("citations", []))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(tool_call.get("id", tool_name)),
                    "content": _tool_content(result),
                }
            )

    return AgentAnswer(
        text=f"Stopped after {max_turns} tool turns before reaching a final answer.",
        citations=_dedupe_citations(citations),
        turns=max_turns,
    )


def _response_message(data: dict[str, Any]) -> dict[str, Any]:
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected chat completion response: {json.dumps(data)[:500]}") from exc
    if not isinstance(message, dict):
        raise RuntimeError("Unexpected chat completion message")
    return message


def _assistant_message(message: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in message.items()
        if key in {"content", "tool_calls", "name"}
    } | {"role": "assistant"}


def _tool_call_parts(tool_call: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    function = tool_call.get("function") or {}
    name = str(function.get("name") or "")
    raw_arguments = function.get("arguments") or "{}"
    try:
        arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    except json.JSONDecodeError:
        arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    return name, arguments


def _tool_content(result: ToolResult) -> str:
    """Keep a tool_result-shaped payload so Paritok can compress the large content."""
    return f"# tool_result {result['name']}\n{result['content']}"


def _bootstrap_search_pattern(question: str) -> str:
    """Turn a question into a broad, safe regex for the first repository search."""
    terms = []
    for term in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", question.lower()):
        if term not in _SEARCH_STOPWORDS and term not in terms:
            terms.append(term)
        if len(terms) == 5:
            break
    return "|".join(re.escape(term) for term in terms) or "TODO|FIXME"


def _dedupe_citations(citations: list[Citation]) -> list[Citation]:
    seen: set[tuple[str, int, int]] = set()
    unique: list[Citation] = []
    for citation in citations:
        try:
            key = (citation["path"], int(citation["start"]), int(citation["end"]))
        except (KeyError, TypeError, ValueError):
            continue
        if key not in seen:
            seen.add(key)
            unique.append(Citation(path=key[0], start=key[1], end=key[2]))
    return unique
